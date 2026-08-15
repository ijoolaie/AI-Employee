"""Pydantic schemas for Run endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    employee_id: UUID
    input_data: dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    employee_version_id: UUID
    employee_name: str | None = None
    employee_slug: str | None = None
    status: str
    input_data: dict[str, Any]
    output_data: dict[str, Any] | None
    error: dict[str, Any] | None
    total_tokens: int
    total_cost_usd: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
