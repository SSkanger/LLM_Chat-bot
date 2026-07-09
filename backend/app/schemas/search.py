from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SearchResult(BaseModel):
    conversation_id: int
    title: str
    matched_content: str
    model_name: str
    prompt_role: str
    updated_at: datetime

