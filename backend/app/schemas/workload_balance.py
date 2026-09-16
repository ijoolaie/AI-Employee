"""Schemas for persisted Stage 9 workload balancing evidence."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkloadBalanceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    target_agent_instance_id: UUID | None
    ready_items: int = Field(ge=0)
    oldest_ready_age_seconds: float = Field(ge=0)
    total_available_slots: int = Field(ge=0)
    queue_pressure: float = Field(ge=0)
    candidates_considered: int = Field(ge=0)
    rationale: list[str]
    contract_version: str
    created_at: datetime
