"""Pydantic response contracts for Run Trace."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    timestamp: datetime


class RunTraceResponse(BaseModel):
    run_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_tokens: int
    total_cost_usd: float
    events: list[TraceEvent]
