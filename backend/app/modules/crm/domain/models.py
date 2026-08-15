from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import uuid

@dataclass(frozen=True)
class Customer:
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    name: str
    email: str | None
    status: str
    metadata: dict[str, Any]

@dataclass(frozen=True)
class Conversation:
    id: uuid.UUID
    customer_id: uuid.UUID
    channel: str
    status: str
    metadata: dict[str, Any]
    last_message_at: datetime | None = None
