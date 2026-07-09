from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.model import ModelConfigOut
from app.services import model_service


router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelConfigOut])
async def list_models(db: Session = Depends(get_db)) -> list[dict]:
    models = model_service.list_available_models(db)
    return [
        {
            "name": item.name,
            "provider": item.provider,
            "model_id": item.model_id,
            "base_url": item.base_url,
            "api_key_env": item.api_key_env,
            "support_stream": item.support_stream,
            "enabled": item.enabled,
            "api_key_configured": model_service.has_api_key(item) or item.provider == "mock",
        }
        for item in models
    ]

