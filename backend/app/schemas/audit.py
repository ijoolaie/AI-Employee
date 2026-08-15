"""Audit log read contracts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_type: str
    actor_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    request_id: str | None
    status: str
    metadata: dict[str, Any] | None
    created_at: datetime
