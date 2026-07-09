from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.prompt import PromptRoleOut
from app.services import prompt_service


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptRoleOut])
async def list_prompt_roles(db: Session = Depends(get_db)) -> list:
    return prompt_service.list_prompt_roles(db)

