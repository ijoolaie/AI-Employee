"""Schemas for Stage 9 telemetry-backed Agent fitness."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentFitnessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_instance_id: UUID
    sample_count: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=1)
    feedback_score: float | None = Field(default=None, ge=0, le=1)
    latency_score: float = Field(ge=0, le=1)
    cost_score: float = Field(ge=0, le=1)
    fitness: float = Field(ge=0, le=1)
    window_start: datetime
    window_end: datetime
    contract_version: str
