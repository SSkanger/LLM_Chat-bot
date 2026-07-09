from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ModelConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    provider: str
    model_id: str
    base_url: str
    api_key_env: str
    support_stream: bool
    enabled: bool
    api_key_configured: bool = False

