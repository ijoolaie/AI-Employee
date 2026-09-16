"""Schemas for Stage 9 workforce capacity forecasting evidence."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CapacityForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    window_days: int = Field(ge=1, le=90)
    horizon_days: int = Field(ge=1, le=30)
    sample_count: int = Field(ge=0)
    demand_samples_per_day: float = Field(ge=0)
    average_run_duration_seconds: float = Field(ge=0)
    current_ready_items: int = Field(ge=0)
    current_active_work_items: int = Field(ge=0)
    total_max_concurrency: int = Field(ge=0)
    total_available_slots: int = Field(ge=0)
    projected_arrivals: float = Field(ge=0)
    projected_required_concurrency: float = Field(ge=0)
    projected_utilization: float = Field(ge=0)
    projected_backlog: float = Field(ge=0)
    lower_bound_required_concurrency: float = Field(ge=0)
    upper_bound_required_concurrency: float = Field(ge=0)
    evidence_complete: bool
    rationale: list[str]
    contract_version: str
    window_start: datetime
    window_end: datetime
