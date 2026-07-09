from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.services import conversation_service


def export_conversation(db: Session, conversation_id: int, user_id: int, fmt: str) -> tuple[str, str, str]:
    conversation = conversation_service.get_conversation(db, conversation_id, user_id)
    normalized = fmt.lower()
    if normalized not in {"markdown", "md", "txt", "json"}:
        raise AppException("UNSUPPORTED_EXPORT_FORMAT", "不支持的导出格式")

    if normalized in {"markdown", "md"}:
        content = _to_markdown(conversation)
        return content, "text/markdown; charset=utf-8", "md"
    if normalized == "txt":
        content = _to_txt(conversation)
        return content, "text/plain; charset=utf-8", "txt"
    content = _to_json(conversation)
    return content, "application/json; charset=utf-8", "json"


def build_export_filename(conversation_id: int, extension: str) -> str:
    date = datetime.utcnow().date().isoformat()
    return f"conversation_{conversation_id}_{date}.{extension}"


def _to_markdown(conversation) -> str:
    lines = [
        f"# {conversation.title}",
        "",
        f"- 创建时间：{conversation.created_at:%Y-%m-%d %H:%M:%S}",
        f"- 更新时间：{conversation.updated_at:%Y-%m-%d %H:%M:%S}",
        f"- 当前模型：{conversation.model_name}",
        f"- 当前角色：{conversation.prompt_role}",
        "",
    ]
    for message in conversation.messages:
        heading = "User" if message.role == "user" else "Assistant"
        meta = ""
        if message.role == "assistant":
            meta = f"（模型：{message.model_name or conversation.model_name}，角色：{message.prompt_role or conversation.prompt_role}）"
        lines.extend([f"## {heading}{meta}", "", message.content, ""])
    return "\n".join(lines)


def _to_txt(conversation) -> str:
    lines = [
        conversation.title,
        f"创建时间：{conversation.created_at:%Y-%m-%d %H:%M:%S}",
        f"当前模型：{conversation.model_name}",
        f"当前角色：{conversation.prompt_role}",
        "",
    ]
    for message in conversation.messages:
        lines.extend([f"[{message.role}] {message.created_at:%Y-%m-%d %H:%M:%S}", message.content, ""])
    return "\n".join(lines)


def _to_json(conversation) -> str:
    payload = {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "model_name": conversation.model_name,
        "prompt_role": conversation.prompt_role,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "model_name": message.model_name,
                "prompt_role": message.prompt_role,
                "created_at": message.created_at.isoformat(),
                "token_count": message.token_count,
                "latency_ms": message.latency_ms,
            }
            for message in conversation.messages
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

