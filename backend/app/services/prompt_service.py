from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.db.models import PromptRole


def list_prompt_roles(db: Session) -> list[PromptRole]:
    return db.query(PromptRole).order_by(PromptRole.name.asc()).all()


def get_prompt_by_role(db: Session, role_name: str) -> PromptRole:
    role = db.query(PromptRole).filter(PromptRole.name == role_name).first()
    if not role:
        raise AppException("PROMPT_ROLE_NOT_FOUND", "指定 Prompt 角色不存在", status_code=404)
    return role

