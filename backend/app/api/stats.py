from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.stats import UserStats
from app.services import stats_service


router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=UserStats)
async def get_stats(user_id: int = Query(...), db: Session = Depends(get_db)) -> dict:
    return stats_service.get_user_stats(db, user_id)

