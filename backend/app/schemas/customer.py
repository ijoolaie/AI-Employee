from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class CustomerResponse(BaseModel):
    id: UUID
    external_key: str
    name: str | None
    email: str | None
    phone: str | None
    tags: list
    notes: str | None
    last_channel: str | None
    created_at: datetime
    updated_at: datetime

class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
