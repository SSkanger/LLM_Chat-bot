from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.search import SearchResult
from app.services import search_service


router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search_conversations(
    user_id: int = Query(...),
    keyword: str = Query(...),
    db: Session = Depends(get_db),
) -> list[dict]:
    return search_service.search_conversations(db, user_id, keyword)

