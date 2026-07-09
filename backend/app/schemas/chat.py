from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int
    conversation_id: int
    message: str = Field(min_length=1)
    model_name: str | None = None
    prompt_role: str | None = None


class ChatResponse(BaseModel):
    answer: str
    model_name: str
    prompt_role: str

