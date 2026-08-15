"""Schemas for Human-in-the-loop Tool approval."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)


class ToolApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    tool_name: str
    tool_call_id: str
    arguments: dict[str, Any]
    status: str
    requested_by: UUID | None
    decided_by: UUID | None
    decision_reason: str | None
    decided_at: datetime | None
    created_at: datetime
