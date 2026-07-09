from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.services import user_service


def get_user_stats(db: Session, user_id: int) -> dict:
    user_service.get_user_by_id(db, user_id)

    conversation_count = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.user_id == user_id, Conversation.is_archived.is_(False))
        .scalar()
        or 0
    )
    message_count = (
        db.query(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id, Conversation.is_archived.is_(False))
        .scalar()
        or 0
    )

    assistant_messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id, Message.role == "assistant", Conversation.is_archived.is_(False))
        .all()
    )
    model_usage = Counter(item.model_name or "unknown" for item in assistant_messages)
    prompt_role_usage = Counter(item.prompt_role or "unknown" for item in assistant_messages)

    start_date = datetime.utcnow().date() - timedelta(days=6)
    recent_messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user_id,
            Conversation.is_archived.is_(False),
            Message.created_at >= datetime.combine(start_date, datetime.min.time()),
        )
        .all()
    )
    recent_7_days = {
        (start_date + timedelta(days=offset)).isoformat(): 0
        for offset in range(7)
    }
    for message in recent_messages:
        key = message.created_at.date().isoformat()
        if key in recent_7_days:
            recent_7_days[key] += 1

    active_rows = (
        db.query(Conversation, func.count(Message.id).label("message_count"))
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id, Conversation.is_archived.is_(False))
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .limit(8)
        .all()
    )
    active_conversations = [
        {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "message_count": count,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
        for conversation, count in active_rows
    ]

    return {
        "conversation_count": conversation_count,
        "message_count": message_count,
        "model_usage": dict(model_usage),
        "prompt_role_usage": dict(prompt_role_usage),
        "recent_7_days": recent_7_days,
        "active_conversations": active_conversations,
    }

