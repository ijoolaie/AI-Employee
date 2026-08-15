from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import uuid

@dataclass(frozen=True)
class WorkflowRun:
    id: uuid.UUID
    workflow_id: uuid.UUID
    tenant_id: uuid.UUID | None
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None = None
