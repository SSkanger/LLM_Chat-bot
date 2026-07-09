from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationCreateResponse,
    ConversationDetail,
    ConversationModelUpdate,
    ConversationPromptRoleUpdate,
    ConversationSummary,
    ConversationTitleUpdate,
)
from app.services import conversation_service


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationCreateResponse)
async def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> dict:
    conversation = conversation_service.create_conversation(
        db,
        user_id=payload.user_id,
        model_name=payload.model_name,
        prompt_role=payload.prompt_role,
    )
    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "model_name": conversation.model_name,
        "prompt_role": conversation.prompt_role,
    }


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    user_id: int = Query(...),
    include_archived: bool = False,
    db: Session = Depends(get_db),
) -> list[dict]:
    return conversation_service.list_conversations(db, user_id, include_archived)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    return conversation_service.get_conversation_detail(db, conversation_id, user_id)


@router.patch("/{conversation_id}/title", response_model=ConversationSummary)
async def rename_conversation(
    conversation_id: int,
    payload: ConversationTitleUpdate,
    db: Session = Depends(get_db),
) -> dict:
    conversation = conversation_service.rename_conversation(db, conversation_id, payload.user_id, payload.title)
    return conversation_service._to_summary(conversation)


@router.patch("/{conversation_id}/model", response_model=ConversationSummary)
async def update_conversation_model(
    conversation_id: int,
    payload: ConversationModelUpdate,
    db: Session = Depends(get_db),
) -> dict:
    conversation = conversation_service.update_conversation_model(
        db,
        conversation_id,
        payload.user_id,
        payload.model_name,
    )
    return conversation_service._to_summary(conversation)


@router.patch("/{conversation_id}/prompt-role", response_model=ConversationSummary)
async def update_conversation_prompt_role(
    conversation_id: int,
    payload: ConversationPromptRoleUpdate,
    db: Session = Depends(get_db),
) -> dict:
    conversation = conversation_service.update_conversation_prompt_role(
        db,
        conversation_id,
        payload.user_id,
        payload.prompt_role,
    )
    return conversation_service._to_summary(conversation)


@router.delete("/{conversation_id}")
async def archive_conversation(
    conversation_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    conversation_service.archive_conversation(db, conversation_id, user_id)
    return {"success": True}

