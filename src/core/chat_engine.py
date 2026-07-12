"""Asynchronous LangChain chat engine with memory, streaming and retries."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config_manager import EnvironmentSettings, ProjectConfig


class StreamingChatModel(Protocol):
    """Minimal LangChain-compatible model contract used by ChatEngine."""

    def astream(self, messages: Sequence[BaseMessage]) -> AsyncIterator[Any]:
        """Stream model chunks asynchronously."""


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
        )


@dataclass(frozen=True)
class ChatResponse:
    content: str
    usage: TokenUsage
    attempts: int


class ChatEngineError(RuntimeError):
    """Raised after a model call cannot be completed."""

    def __init__(self, message: str, *, attempts: int, partial_response: str = "") -> None:
        super().__init__(message)
        self.attempts = attempts
        self.partial_response = partial_response


class TokenCounter:
    """Count tokens locally when a provider does not return stream usage."""

    def __init__(self) -> None:
        self._encoding: Any | None = None
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return max(1, (len(text) + 3) // 4)

    def count_messages(self, messages: Sequence[BaseMessage]) -> int:
        return sum(self.count(_content_to_text(message.content)) + 4 for message in messages)


class MockStreamingChatModel:
    """Offline LangChain-compatible model used for tests and course demos."""

    def __init__(self, model_name: str = "mock") -> None:
        self.model_name = model_name

    async def astream(self, messages: Sequence[BaseMessage]) -> AsyncIterator[AIMessageChunk]:
        user_messages = [
            _content_to_text(message.content)
            for message in messages
            if isinstance(message, HumanMessage)
        ]
        latest = user_messages[-1] if user_messages else ""
        response = (
            f"【mock 模型：{self.model_name}】已收到：{latest}。"
            f"当前上下文包含 {max(0, len(user_messages) - 1)} 轮历史提问。"
        )
        for index in range(0, len(response), 6):
            await asyncio.sleep(0)
            yield AIMessageChunk(content=response[index : index + 6])


class ChatEngine:
    """UI-independent multi-turn streaming conversation engine."""

    def __init__(
        self,
        model: StreamingChatModel,
        *,
        model_name: str,
        system_prompt: str = "",
        timeout_seconds: float = 30,
        max_retries: int = 3,
        max_context_messages: int = 20,
        retry_delay_seconds: float = 0.1,
        memory: InMemoryChatMessageHistory | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds 必须大于 0")
        if max_retries < 0:
            raise ValueError("max_retries 不能小于 0")
        self.model = model
        self.model_name = model_name
        self.system_prompt = system_prompt.strip()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_context_messages = max_context_messages
        self.retry_delay_seconds = retry_delay_seconds
        self.memory = memory or InMemoryChatMessageHistory()
        self.token_counter = token_counter or TokenCounter()
        self.last_usage = TokenUsage()
        self.total_usage = TokenUsage()
        self.last_attempts = 0

    @classmethod
    def from_config(
        cls,
        config: ProjectConfig,
        environment: EnvironmentSettings,
        *,
        system_prompt: str = "",
    ) -> ChatEngine:
        model_name = environment.model_name or config.llm.default_model
        model_definition = _find_model_definition(config.models, model_name)
        model_id = str(model_definition.get("model_id", model_name))
        base_url = environment.api_base_url or str(model_definition.get("base_url", ""))
        key_name = str(model_definition.get("api_key_env", ""))
        api_key = environment.api_key or (os.getenv(key_name, "") if key_name else "")
        provider = str(model_definition.get("provider", "mock" if model_name == "mock" else ""))

        if provider == "mock" or model_name == "mock" or not api_key:
            model: StreamingChatModel = MockStreamingChatModel(model_name)
        else:
            model = ChatOpenAI(
                model=model_id,
                api_key=api_key,
                base_url=base_url or None,
                streaming=True,
                stream_usage=True,
                timeout=config.llm.timeout_seconds,
                max_retries=0,
            )
        return cls(
            model,
            model_name=model_name,
            system_prompt=system_prompt,
            timeout_seconds=config.llm.timeout_seconds,
            max_retries=config.llm.max_retries,
            max_context_messages=config.llm.max_context_messages,
        )

    async def astream(self, user_input: str) -> AsyncIterator[str]:
        normalized_input = user_input.strip()
        if not normalized_input:
            raise ValueError("用户消息不能为空")

        human_message = HumanMessage(content=normalized_input)
        history = list(self.memory.messages)[-self.max_context_messages :]
        messages: list[BaseMessage] = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        messages.extend(history)
        messages.append(human_message)

        max_attempts = self.max_retries + 1
        for attempt in range(1, max_attempts + 1):
            parts: list[str] = []
            provider_usage = TokenUsage()
            emitted = False
            try:
                iterator = self.model.astream(messages).__aiter__()
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            iterator.__anext__(), timeout=self.timeout_seconds
                        )
                    except StopAsyncIteration:
                        break
                    text = _content_to_text(getattr(chunk, "content", chunk))
                    usage = _extract_usage(chunk)
                    if usage.total_tokens:
                        provider_usage = usage
                    if text:
                        emitted = True
                        parts.append(text)
                        yield text

                answer = "".join(parts)
                if not answer:
                    raise RuntimeError("模型未返回任何内容")
                usage = provider_usage
                if usage.total_tokens == 0:
                    usage = TokenUsage(
                        prompt_tokens=self.token_counter.count_messages(messages),
                        completion_tokens=self.token_counter.count(answer),
                    )
                self.memory.add_messages([human_message, AIMessage(content=answer)])
                self.last_usage = usage
                self.total_usage = self.total_usage + usage
                self.last_attempts = attempt
                return
            except Exception as exc:
                partial = "".join(parts)
                if emitted or attempt >= max_attempts:
                    self.last_attempts = attempt
                    raise ChatEngineError(
                        f"模型调用失败（已尝试 {attempt} 次）：{exc}",
                        attempts=attempt,
                        partial_response=partial,
                    ) from exc
                await asyncio.sleep(self.retry_delay_seconds * (2 ** (attempt - 1)))

    async def ainvoke(self, user_input: str) -> ChatResponse:
        chunks = [chunk async for chunk in self.astream(user_input)]
        return ChatResponse("".join(chunks), self.last_usage, self.last_attempts)

    def history_messages(self) -> list[BaseMessage]:
        return list(self.memory.messages)

    def reset(self) -> None:
        self.memory.clear()
        self.last_usage = TokenUsage()
        self.total_usage = TokenUsage()
        self.last_attempts = 0

    def set_system_prompt(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt.strip()


def _find_model_definition(
    definitions: list[dict[str, Any]] | dict[str, Any], model_name: str
) -> dict[str, Any]:
    if isinstance(definitions, list):
        return next((item for item in definitions if item.get("name") == model_name), {})
    available = definitions.get("available", [])
    if isinstance(available, list):
        return next(
            (item for item in available if item.get("value") == model_name or item.get("name") == model_name),
            {},
        )
    return {}


def _extract_usage(chunk: Any) -> TokenUsage:
    metadata = getattr(chunk, "usage_metadata", None) or {}
    if not isinstance(metadata, dict):
        return TokenUsage()
    return TokenUsage(
        prompt_tokens=int(metadata.get("input_tokens", metadata.get("prompt_tokens", 0)) or 0),
        completion_tokens=int(
            metadata.get("output_tokens", metadata.get("completion_tokens", 0)) or 0
        ),
    )


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)
