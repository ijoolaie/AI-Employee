"""Schemas for Stage 9 Agent version promotion evidence."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentPromotionEvidenceResponse(BaseModel):
    """Read-only comparison evidence for a candidate AgentTemplate version."""

    model_config = ConfigDict(from_attributes=True)

    candidate_agent_template_id: UUID
    candidate_slug: str
    candidate_version: int = Field(ge=1)
    candidate_sample_count: int = Field(ge=0)
    candidate_fitness: float = Field(ge=0, le=1)
    baseline_agent_template_id: UUID | None = None
    baseline_version: int | None = Field(default=None, ge=1)
    baseline_sample_count: int = Field(ge=0)
    baseline_fitness: float | None = Field(default=None, ge=0, le=1)
    fitness_delta: float | None = None
    comparable: bool
    evidence_window_start: datetime
    evidence_window_end: datetime
    contract_version: str
