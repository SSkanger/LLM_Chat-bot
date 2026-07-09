from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppException
from app.db.models import Conversation
from app.services import model_service, prompt_service, user_service


def _to_summary(conversation: Conversation) -> dict:
    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "model_name": conversation.model_name,
        "prompt_role": conversation.prompt_role,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "is_archived": conversation.is_archived,
    }


def create_conversation(db: Session, user_id: int, model_name: str, prompt_role: str) -> Conversation:
    user_service.get_user_by_id(db, user_id)
    model_service.get_model_config(db, model_name)
    prompt_service.get_prompt_by_role(db, prompt_role)

    conversation = Conversation(
        user_id=user_id,
        title="新会话",
        model_name=model_name,
        prompt_role=prompt_role,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session, user_id: int, include_archived: bool = False) -> list[dict]:
    user_service.get_user_by_id(db, user_id)
    query = db.query(Conversation).filter(Conversation.user_id == user_id)
    if not include_archived:
        query = query.filter(Conversation.is_archived.is_(False))
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return [_to_summary(item) for item in conversations]


def get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conversation = (
        db.query(Conversation)
        .options(selectinload(Conversation.messages))
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conversation:
        raise AppException("CONVERSATION_NOT_FOUND", "会话不存在或不属于当前用户", status_code=404)
    return conversation


def get_conversation_detail(db: Session, conversation_id: int, user_id: int) -> dict:
    conversation = get_conversation(db, conversation_id, user_id)
    data = _to_summary(conversation)
    data["messages"] = conversation.messages
    return data


def rename_conversation(db: Session, conversation_id: int, user_id: int, title: str) -> Conversation:
    conversation = get_conversation(db, conversation_id, user_id)
    conversation.title = title.strip()
    db.commit()
    db.refresh(conversation)
    return conversation


def update_conversation_model(db: Session, conversation_id: int, user_id: int, model_name: str) -> Conversation:
    conversation = get_conversation(db, conversation_id, user_id)
    model_service.get_model_config(db, model_name)
    conversation.model_name = model_name
    db.commit()
    db.refresh(conversation)
    return conversation


def update_conversation_prompt_role(db: Session, conversation_id: int, user_id: int, prompt_role: str) -> Conversation:
    conversation = get_conversation(db, conversation_id, user_id)
    prompt_service.get_prompt_by_role(db, prompt_role)
    conversation.prompt_role = prompt_role
    db.commit()
    db.refresh(conversation)
    return conversation


def archive_conversation(db: Session, conversation_id: int, user_id: int) -> None:
    conversation = get_conversation(db, conversation_id, user_id)
    conversation.is_archived = True
    db.commit()

