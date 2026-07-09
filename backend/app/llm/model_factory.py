from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from app.core.config import get_settings
from app.db.models import ModelConfig


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class ChatModel(Protocol):
    async def ainvoke(self, messages: list[ChatMessage]) -> str:
        ...

    async def astream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        ...


class MockChatModel:
    def __init__(self, model_name: str = "mock", reason: str | None = None) -> None:
        self.model_name = model_name
        self.reason = reason

    async def ainvoke(self, messages: list[ChatMessage]) -> str:
        await asyncio.sleep(0.05)
        user_message = next((item.content for item in reversed(messages) if item.role == "user"), "")
        system_prompt = next((item.content for item in messages if item.role == "system"), "")
        context_count = len([item for item in messages if item.role in {"user", "assistant"}])
        prefix = f"【mock 模型：{self.model_name}】"
        if self.reason:
            prefix += f"（{self.reason}）"
        return (
            f"{prefix}\n\n"
            f"我已收到你的问题：{user_message}\n\n"
            f"当前会话携带了 {context_count} 条上下文消息。"
            f"我会按照当前角色要求回答：{system_prompt[:80]}"
        )

    async def astream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        answer = await self.ainvoke(messages)
        for char in answer:
            await asyncio.sleep(0.002)
            yield char


class LangChainChatModelAdapter:
    def __init__(self, model: object) -> None:
        self.model = model

    async def ainvoke(self, messages: list[ChatMessage]) -> str:
        result = await self.model.ainvoke(_to_langchain_messages(messages))
        return _content_to_text(getattr(result, "content", result))

    async def astream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        async for chunk in self.model.astream(_to_langchain_messages(messages)):
            text = _content_to_text(getattr(chunk, "content", chunk))
            if text:
                yield text


def build_chat_model(model_config: ModelConfig, streaming: bool = True) -> ChatModel:
    if model_config.provider == "mock":
        return MockChatModel(model_config.name)

    if model_config.provider == "openai-compatible":
        api_key = os.getenv(model_config.api_key_env) if model_config.api_key_env else None
        if not api_key:
            return MockChatModel(model_config.name, "未配置 API Key，已自动使用本地 mock 兜底")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return MockChatModel(model_config.name, "缺少 langchain-openai 依赖，已自动使用本地 mock 兜底")

        settings = get_settings()
        model = ChatOpenAI(
            model=model_config.model_id,
            api_key=api_key,
            base_url=model_config.base_url or None,
            streaming=streaming,
            timeout=settings.llm.timeout_seconds,
            max_retries=0,
        )
        return LangChainChatModelAdapter(model)

    return MockChatModel(model_config.name, f"暂不支持 provider={model_config.provider}")


def _to_langchain_messages(messages: list[ChatMessage]) -> list[object]:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    converted: list[object] = []
    for message in messages:
        if message.role == "system":
            converted.append(SystemMessage(content=message.content))
        elif message.role == "assistant":
            converted.append(AIMessage(content=message.content))
        else:
            converted.append(HumanMessage(content=message.content))
    return converted


def _content_to_text(content: object) -> str:
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
