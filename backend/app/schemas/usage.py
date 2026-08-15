"""Usage and cost reporting contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UsageBreakdown(BaseModel):
    provider: str
    model: str
    calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    avg_latency_ms: float = Field(ge=0)


class UsageSummaryResponse(BaseModel):
    from_at: datetime | None
    to_at: datetime | None
    calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    avg_latency_ms: float = Field(ge=0)
    breakdown: list[UsageBreakdown]
    notes: list[str] = []
