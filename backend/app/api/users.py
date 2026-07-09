from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut
from app.services import user_service


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut)
async def create_or_get_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    return user_service.get_or_create_user(db, payload.username)

