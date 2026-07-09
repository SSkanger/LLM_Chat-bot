from __future__ import annotations

import os

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.db.models import ModelConfig


def list_available_models(db: Session) -> list[ModelConfig]:
    return (
        db.query(ModelConfig)
        .filter(ModelConfig.enabled.is_(True))
        .order_by(ModelConfig.name.asc())
        .all()
    )


def get_model_config(db: Session, model_name: str) -> ModelConfig:
    model = (
        db.query(ModelConfig)
        .filter(ModelConfig.name == model_name, ModelConfig.enabled.is_(True))
        .first()
    )
    if not model:
        raise AppException("MODEL_NOT_FOUND", "指定模型不存在", status_code=404)
    return model


def has_api_key(model: ModelConfig) -> bool:
    return bool(model.api_key_env and os.getenv(model.api_key_env))

