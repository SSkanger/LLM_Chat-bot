from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(payload: ChatRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    return await chat_service.send_message(
        db,
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        content=payload.message,
        model_name=payload.model_name,
        prompt_role=payload.prompt_role,
    )


@router.post("/stream")
async def stream_message(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    return StreamingResponse(
        chat_service.stream_message(
            db,
            conversation_id=payload.conversation_id,
            user_id=payload.user_id,
            content=payload.message,
            model_name=payload.model_name,
            prompt_role=payload.prompt_role,
        ),
        media_type="text/plain; charset=utf-8",
    )

