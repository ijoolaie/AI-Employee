"""Schemas for Stage 9 Agent-template-version fitness."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentVersionFitnessResponse(BaseModel):
    """Read-only fitness snapshot grouped by immutable AgentTemplate version."""

    model_config = ConfigDict(from_attributes=True)

    agent_template_id: UUID
    agent_instance_count: int = Field(ge=1)
    slug: str
    version: int = Field(ge=1)
    sample_count: int = Field(ge=1)
    success_rate: float = Field(ge=0, le=1)
    feedback_score: float | None = Field(default=None, ge=0, le=1)
    latency_score: float = Field(ge=0, le=1)
    cost_score: float = Field(ge=0, le=1)
    fitness: float = Field(ge=0, le=1)
    window_start: datetime
    window_end: datetime
    contract_version: str
