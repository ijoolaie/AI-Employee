from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

@dataclass(frozen=True)
class Notification:
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    kind: str
    read: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
