from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"


class AppSettings(BaseModel):
    name: str = "LLM Chat-bot"
    debug: bool = True


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./backend/data/chatbot.db"


class LLMSettings(BaseModel):
    default_model: str = "mock"
    timeout_seconds: int = 60
    max_retries: int = 2
    max_context_messages: int = 20
    stream: bool = True


class ModelSettings(BaseModel):
    name: str
    provider: str
    model_id: str
    base_url: str = ""
    api_key_env: str = ""
    support_stream: bool = True
    enabled: bool = True


class PromptRoleSettings(BaseModel):
    name: str
    description: str = ""
    system_prompt: str


class Settings(BaseModel):
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    models: list[ModelSettings] = Field(default_factory=list)
    prompt_roles: list[PromptRoleSettings] = Field(default_factory=list)
    log_level: str = "INFO"


def _load_yaml_config() -> dict[str, Any]:
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _normalize_sqlite_url(url: str) -> str:
    if not url.startswith("sqlite:///./"):
        return url
    relative_path = url.removeprefix("sqlite:///./")
    absolute_path = (PROJECT_ROOT / relative_path).resolve()
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{absolute_path.as_posix()}"


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    database = data.setdefault("database", {})
    llm = data.setdefault("llm", {})

    if os.getenv("DATABASE_URL"):
        database["url"] = os.environ["DATABASE_URL"]
    if os.getenv("DEFAULT_MODEL"):
        llm["default_model"] = os.environ["DEFAULT_MODEL"]
    data["log_level"] = os.getenv("LOG_LEVEL", data.get("log_level", "INFO"))
    database["url"] = _normalize_sqlite_url(database.get("url", "sqlite:///./backend/data/chatbot.db"))
    return data


@lru_cache
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BACKEND_DIR / ".env")
    data = _apply_env_overrides(_load_yaml_config())
    return Settings(**data)

