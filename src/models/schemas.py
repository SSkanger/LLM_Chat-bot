"""Validated data structures shared by storage, business and UI layers."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class MessageRole(str, Enum):
    """Roles accepted by the conversation message model."""

    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


class EntityModel(BaseModel):
    """Common validation behavior for persisted entities."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)


class User(EntityModel):
    id: int | None = None
    username: str = Field(min_length=1, max_length=64)
    default_model: str = Field(default="deepseek-chat", min_length=1, max_length=100)
    default_preset_id: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("用户名不能为空")
        return normalized


class Session(EntityModel):
    id: int | None = None
    user_id: int
    title: str = Field(default="新会话", min_length=1, max_length=200)
    model_name: str = Field(default="deepseek-chat", min_length=1, max_length=100)
    preset_id: int | None = None
    total_prompt_tokens: int = Field(default=0, ge=0)
    total_completion_tokens: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Message(EntityModel):
    id: int | None = None
    session_id: int
    role: MessageRole
    content: str = Field(min_length=1)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("消息内容不能为空")
        return value


class Preset(EntityModel):
    id: int | None = None
    user_id: int | None = None
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(min_length=1)
    is_builtin: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class UserConfig(EntityModel):
    id: int | None = None
    user_id: int
    key: str = Field(min_length=1, max_length=100)
    value: str = ""
    updated_at: datetime = Field(default_factory=utc_now)
