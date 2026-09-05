from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class UsageBudgetResponse(BaseModel):
    state: str
    run_utilization: float = Field(ge=0)
    token_utilization: float = Field(ge=0)
    remaining_runs: int = Field(ge=0)
    remaining_tokens: int = Field(ge=0)


class UsageOptimizationResponse(BaseModel):
    period_start: datetime
    plan: str
    usage: dict[str, int]
    cost_usd: float = Field(ge=0)
    successful_work_items: int = Field(ge=0)
    cost_per_successful_work_item_usd: float = Field(ge=0)
    budget: UsageBudgetResponse
    optimization_actions: list[str]
