from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.models import Conversation, Message, RequestLog
from app.llm.model_factory import ChatMessage, build_chat_model
from app.services import conversation_service, model_service, prompt_service


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _auto_title(message: str) -> str:
    title = " ".join(message.strip().split())
    return (title[:20] + "...") if len(title) > 20 else title or "新会话"


def _save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    model_name: str | None = None,
    prompt_role: str | None = None,
    latency_ms: int | None = None,
    error_message: str | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model_name=model_name,
        prompt_role=prompt_role,
        token_count=_estimate_tokens(content),
        latency_ms=latency_ms,
        error_message=error_message,
    )
    db.add(message)
    return message


def _prepare_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
    model_name: str | None,
    prompt_role: str | None,
) -> tuple[Conversation, str, str]:
    conversation = conversation_service.get_conversation(db, conversation_id, user_id)
    active_model = model_name or conversation.model_name
    active_role = prompt_role or conversation.prompt_role

    model_service.get_model_config(db, active_model)
    prompt_service.get_prompt_by_role(db, active_role)

    if conversation.model_name != active_model:
        conversation.model_name = active_model
    if conversation.prompt_role != active_role:
        conversation.prompt_role = active_role
    return conversation, active_model, active_role


def _build_messages(db: Session, conversation_id: int, prompt_role: str) -> list[ChatMessage]:
    settings = get_settings()
    role = prompt_service.get_prompt_by_role(db, prompt_role)
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(settings.llm.max_context_messages)
        .all()
    )
    ordered_history = list(reversed(history))
    messages = [ChatMessage(role="system", content=role.system_prompt)]
    messages.extend(ChatMessage(role=item.role, content=item.content) for item in ordered_history)
    return messages


async def _invoke_with_retry(chat_model: object, messages: list[ChatMessage]) -> str:
    settings = get_settings()
    attempts = settings.llm.max_retries + 1
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempts),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(chat_model.ainvoke(messages), timeout=settings.llm.timeout_seconds)
    raise RuntimeError("LLM invocation failed")


async def _stream_with_timeout(chat_model: object, messages: list[ChatMessage]) -> AsyncIterator[str]:
    settings = get_settings()
    iterator = chat_model.astream(messages).__aiter__()
    while True:
        try:
            chunk = await asyncio.wait_for(iterator.__anext__(), timeout=settings.llm.timeout_seconds)
        except StopAsyncIteration:
            break
        yield chunk


def _write_request_log(
    db: Session,
    user_id: int,
    conversation_id: int,
    model_name: str,
    prompt_role: str,
    request_text: str,
    success: bool,
    latency_ms: int,
    error: Exception | None = None,
) -> None:
    log = RequestLog(
        user_id=user_id,
        conversation_id=conversation_id,
        model_name=model_name,
        prompt_role=prompt_role,
        request_text=request_text[:1000],
        success=success,
        latency_ms=latency_ms,
        error_type=type(error).__name__ if error else None,
        error_message=str(error)[:1000] if error else None,
    )
    db.add(log)
    event = "llm_request" if success else "llm_request_error"
    logger.bind(
        event=event,
        user_id=user_id,
        conversation_id=conversation_id,
        model_name=model_name,
        prompt_role=prompt_role,
        success=success,
        latency_ms=latency_ms,
        error_type=type(error).__name__ if error else None,
    ).info(event)


def _maybe_update_title(db: Session, conversation: Conversation, user_message: str) -> None:
    user_message_count = (
        db.query(func.count(Message.id))
        .filter(Message.conversation_id == conversation.id, Message.role == "user")
        .scalar()
    )
    if conversation.title == "新会话" and user_message_count == 1:
        conversation.title = _auto_title(user_message)


async def send_message(
    db: Session,
    conversation_id: int,
    user_id: int,
    content: str,
    model_name: str | None = None,
    prompt_role: str | None = None,
) -> dict[str, str]:
    conversation, active_model, active_role = _prepare_conversation(db, conversation_id, user_id, model_name, prompt_role)
    _save_message(db, conversation.id, "user", content)
    _maybe_update_title(db, conversation, content)
    db.commit()

    model_config = model_service.get_model_config(db, active_model)
    chat_model = build_chat_model(model_config, streaming=False)
    messages = _build_messages(db, conversation.id, active_role)
    start = time.perf_counter()

    try:
        answer = await _invoke_with_retry(chat_model, messages)
        latency_ms = int((time.perf_counter() - start) * 1000)
        _save_message(db, conversation.id, "assistant", answer, active_model, active_role, latency_ms)
        _write_request_log(db, user_id, conversation.id, active_model, active_role, content, True, latency_ms)
        db.commit()
        return {"answer": answer, "model_name": active_model, "prompt_role": active_role}
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        safe_message = "模型调用失败，请稍后重试或切换 mock 模型。"
        _save_message(db, conversation.id, "assistant", safe_message, active_model, active_role, latency_ms, str(exc))
        _write_request_log(db, user_id, conversation.id, active_model, active_role, content, False, latency_ms, exc)
        db.commit()
        raise AppException("LLM_REQUEST_FAILED", safe_message, status_code=502) from exc


async def stream_message(
    db: Session,
    conversation_id: int,
    user_id: int,
    content: str,
    model_name: str | None = None,
    prompt_role: str | None = None,
) -> AsyncIterator[str]:
    conversation, active_model, active_role = _prepare_conversation(db, conversation_id, user_id, model_name, prompt_role)
    _save_message(db, conversation.id, "user", content)
    _maybe_update_title(db, conversation, content)
    db.commit()

    model_config = model_service.get_model_config(db, active_model)
    chat_model = build_chat_model(model_config, streaming=True)
    messages = _build_messages(db, conversation.id, active_role)
    start = time.perf_counter()
    chunks: list[str] = []

    try:
        async for chunk in _stream_with_timeout(chat_model, messages):
            chunks.append(chunk)
            yield chunk
        answer = "".join(chunks)
        latency_ms = int((time.perf_counter() - start) * 1000)
        _save_message(db, conversation.id, "assistant", answer, active_model, active_role, latency_ms)
        _write_request_log(db, user_id, conversation.id, active_model, active_role, content, True, latency_ms)
        db.commit()
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        safe_message = "\n\n模型调用失败，请稍后重试或切换 mock 模型。"
        _save_message(db, conversation.id, "assistant", safe_message.strip(), active_model, active_role, latency_ms, str(exc))
        _write_request_log(db, user_id, conversation.id, active_model, active_role, content, False, latency_ms, exc)
        db.commit()
        yield safe_message

