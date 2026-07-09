from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.db.models import User


def get_or_create_user(db: Session, username: str) -> User:
    normalized = username.strip()
    if not normalized:
        raise AppException("INVALID_USERNAME", "用户名不能为空")

    user = db.query(User).filter(User.username == normalized).first()
    if user:
        return user

    user = User(username=normalized)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise AppException("USER_NOT_FOUND", "用户不存在", status_code=404)
    return user

