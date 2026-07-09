from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ActiveConversation(BaseModel):
    conversation_id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class UserStats(BaseModel):
    conversation_count: int
    message_count: int
    model_usage: dict[str, int]
    prompt_role_usage: dict[str, int]
    recent_7_days: dict[str, int]
    active_conversations: list[ActiveConversation]

