"""Typed configuration loading for YAML and environment variables."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EnvironmentSettings(BaseSettings):
    """Sensitive and environment-specific values loaded from process env."""

    app_env: str = "dev"
    api_base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    mysql_password: str = ""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"dev", "test", "prod"}:
            raise ValueError("APP_ENV 必须是 dev、test 或 prod")
        return normalized


class AppSection(BaseModel):
    name: str = "langchain-chat"
    version: str = "0.1.0"
    debug: bool = True
    env: str = "dev"

    model_config = ConfigDict(extra="allow")


class StorageSection(BaseModel):
    type: str = "sqlite"
    sqlite: dict[str, Any] = Field(default_factory=dict)
    mysql: dict[str, Any] = Field(default_factory=dict)
    file: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class LLMSection(BaseModel):
    default_model: str = "mock"
    timeout_seconds: int = Field(default=60, gt=0)
    max_retries: int = Field(default=2, ge=0)
    max_context_messages: int = Field(default=20, gt=0)
    stream: bool = True

    model_config = ConfigDict(extra="allow")


class ProjectConfig(BaseModel):
    app: AppSection = Field(default_factory=AppSection)
    storage: StorageSection = Field(default_factory=StorageSection)
    llm: LLMSection = Field(default_factory=LLMSection)
    models: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=list)
    database: dict[str, Any] = Field(default_factory=dict)
    session: dict[str, Any] = Field(default_factory=dict)
    export: dict[str, Any] = Field(default_factory=dict)
    prompt_roles: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge environment overrides into a base mapping."""
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ConfigManager:
    """Load, validate and expose project configuration."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = (project_root or PROJECT_ROOT).resolve()
        self._config: ProjectConfig | None = None
        self.environment: EnvironmentSettings | None = None

    def load(self) -> ProjectConfig:
        load_dotenv(self.project_root / ".env", override=False)
        environment = EnvironmentSettings()
        base = self._read_yaml(self.project_root / "config.yaml")
        override_path = self.project_root / f"config.{environment.app_env}.yaml"
        merged = deep_merge(base, self._read_yaml(override_path))
        merged.setdefault("app", {})["env"] = environment.app_env

        llm = merged.setdefault("llm", {})
        if environment.model_name:
            llm["default_model"] = environment.model_name

        mysql = merged.setdefault("storage", {}).setdefault("mysql", {})
        if environment.mysql_password:
            mysql["password"] = environment.mysql_password

        self.environment = environment
        self._config = ProjectConfig.model_validate(merged)
        return self._config

    @property
    def config(self) -> ProjectConfig:
        return self._config or self.load()

    def load_presets(self) -> list[dict[str, Any]]:
        data = self._read_yaml(self.project_root / "config" / "presets.yaml")
        presets = data.get("presets", [])
        if not isinstance(presets, list):
            raise ValueError("config/presets.yaml 中的 presets 必须是列表")
        return presets

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError(f"配置文件顶层必须是映射：{path}")
        return data
