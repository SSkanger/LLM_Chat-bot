from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    user_id: int
    model_name: str
    prompt_role: str


class ConversationTitleUpdate(BaseModel):
    user_id: int
    title: str = Field(min_length=1, max_length=200)


class ConversationModelUpdate(BaseModel):
    user_id: int
    model_name: str


class ConversationPromptRoleUpdate(BaseModel):
    user_id: int
    prompt_role: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    model_name: str | None = None
    prompt_role: str | None = None
    created_at: datetime
    token_count: int | None = None
    latency_ms: int | None = None
    error_message: str | None = None


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    title: str
    model_name: str
    prompt_role: str
    updated_at: datetime
    created_at: datetime
    is_archived: bool


class ConversationDetail(ConversationSummary):
    messages: list[MessageOut]


class ConversationCreateResponse(BaseModel):
    conversation_id: int
    title: str
    model_name: str
    prompt_role: str

