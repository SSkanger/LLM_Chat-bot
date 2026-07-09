from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import export_service


router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{conversation_id}")
async def export_conversation(
    conversation_id: int,
    user_id: int = Query(...),
    format: str = Query("markdown"),
    db: Session = Depends(get_db),
) -> Response:
    content, media_type, extension = export_service.export_conversation(db, conversation_id, user_id, format)
    filename = export_service.build_export_filename(conversation_id, extension)
    encoded_filename = quote(filename)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )

