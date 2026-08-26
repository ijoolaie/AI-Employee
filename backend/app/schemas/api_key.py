from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    expires_at: datetime | None = None
    scopes: list[str] | None = Field(default=None, max_length=100)


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    scopes: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    key: str
