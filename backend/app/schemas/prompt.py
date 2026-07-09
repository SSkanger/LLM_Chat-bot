from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PromptRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    system_prompt: str

