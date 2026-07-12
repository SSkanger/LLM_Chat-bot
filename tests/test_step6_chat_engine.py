import asyncio
from collections.abc import AsyncIterator, Sequence

import pytest
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage

from core.chat_engine import ChatEngine, ChatEngineError, MockStreamingChatModel


class RecordingModel:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[list[BaseMessage]] = []

    async def astream(self, messages: Sequence[BaseMessage]) -> AsyncIterator[AIMessageChunk]:
        self.calls.append(list(messages))
        response = self.responses[len(self.calls) - 1]
        for part in response.split("|"):
            yield AIMessageChunk(content=part)


class FlakyModel:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    async def astream(self, messages: Sequence[BaseMessage]) -> AsyncIterator[AIMessageChunk]:
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError("temporary failure")
        yield AIMessageChunk(content="重试成功")


class SlowModel:
    def __init__(self) -> None:
        self.calls = 0

    async def astream(self, messages: Sequence[BaseMessage]) -> AsyncIterator[AIMessageChunk]:
        self.calls += 1
        await asyncio.sleep(0.05)
        yield AIMessageChunk(content="too late")


@pytest.mark.asyncio
async def test_multiturn_memory_and_system_prompt() -> None:
    model = RecordingModel(["第一|次回答", "第二次回答"])
    engine = ChatEngine(model, model_name="recording", system_prompt="系统角色")

    first = await engine.ainvoke("第一个问题")
    second = await engine.ainvoke("第二个问题")

    assert first.content == "第一次回答"
    assert second.content == "第二次回答"
    assert isinstance(model.calls[0][0], SystemMessage)
    assert len(model.calls[0]) == 2
    assert len(model.calls[1]) == 4
    assert isinstance(model.calls[1][-1], HumanMessage)
    assert len(engine.history_messages()) == 4


@pytest.mark.asyncio
async def test_streaming_and_token_statistics() -> None:
    engine = ChatEngine(RecordingModel(["流式|输出"]), model_name="recording")
    chunks = [chunk async for chunk in engine.astream("测试流式")]

    assert chunks == ["流式", "输出"]
    assert engine.last_usage.prompt_tokens > 0
    assert engine.last_usage.completion_tokens > 0
    assert engine.total_usage == engine.last_usage


@pytest.mark.asyncio
async def test_retry_before_first_chunk() -> None:
    model = FlakyModel(failures=1)
    engine = ChatEngine(
        model,
        model_name="flaky",
        max_retries=2,
        retry_delay_seconds=0,
    )

    response = await engine.ainvoke("请重试")
    assert response.content == "重试成功"
    assert response.attempts == 2
    assert model.calls == 2


@pytest.mark.asyncio
async def test_timeout_retries_then_raises() -> None:
    model = SlowModel()
    engine = ChatEngine(
        model,
        model_name="slow",
        timeout_seconds=0.01,
        max_retries=1,
        retry_delay_seconds=0,
    )

    with pytest.raises(ChatEngineError) as error:
        await engine.ainvoke("触发超时")
    assert error.value.attempts == 2
    assert model.calls == 2
    assert engine.history_messages() == []


@pytest.mark.asyncio
async def test_mock_model_supports_multiple_turns() -> None:
    engine = ChatEngine(MockStreamingChatModel(), model_name="mock")
    await engine.ainvoke("第一轮")
    response = await engine.ainvoke("第二轮")
    assert "1 轮历史提问" in response.content


def test_reset_clears_memory_and_usage() -> None:
    engine = ChatEngine(MockStreamingChatModel(), model_name="mock")
    engine.reset()
    assert engine.history_messages() == []
    assert engine.total_usage.total_tokens == 0
