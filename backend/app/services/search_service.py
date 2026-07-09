from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.db.models import Conversation, Message
from app.services import user_service


def search_conversations(db: Session, user_id: int, keyword: str) -> list[dict]:
    user_service.get_user_by_id(db, user_id)
    normalized = keyword.strip()
    if not normalized:
        raise AppException("EMPTY_KEYWORD", "搜索关键词不能为空")

    pattern = f"%{normalized}%"
    rows = (
        db.query(Conversation, Message)
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user_id,
            Conversation.is_archived.is_(False),
            or_(
                Conversation.title.like(pattern),
                Conversation.model_name.like(pattern),
                Conversation.prompt_role.like(pattern),
                Message.content.like(pattern),
            ),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(100)
        .all()
    )

    results: dict[int, dict] = {}
    for conversation, message in rows:
        if conversation.id in results:
            continue
        matched_content = conversation.title
        if message and normalized.lower() in message.content.lower():
            matched_content = message.content[:160]
        results[conversation.id] = {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "matched_content": matched_content,
            "model_name": conversation.model_name,
            "prompt_role": conversation.prompt_role,
            "updated_at": conversation.updated_at,
        }
    return list(results.values())

