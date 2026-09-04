from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AdminTenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    users: int = Field(ge=0)
    workflows: int = Field(ge=0)
    runs: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    created_at: datetime


class AdminProviderSummary(BaseModel):
    provider: str
    calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    avg_latency_ms: float = Field(ge=0)


class AdminHealthSummary(BaseModel):
    database: str
    redis: str
    celery: str
    ai_provider: str


class AdminDashboardResponse(BaseModel):
    tenants: int = Field(ge=0)
    active_tenants: int = Field(ge=0)
    users: int = Field(ge=0)
    workflows: int = Field(ge=0)
    workflow_runs: int = Field(ge=0)
    ai_calls: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    failed_runs: int = Field(ge=0)
    pending_outbox: int = Field(ge=0)
    dead_outbox: int = Field(ge=0)
    tenants_breakdown: list[AdminTenantSummary]
    providers: list[AdminProviderSummary]
    health: AdminHealthSummary


class AdminTenantListResponse(BaseModel):
    items: list[AdminTenantSummary]


class AdminOptimizationBudget(BaseModel):
    state: str
    run_utilization: float = Field(ge=0)
    token_utilization: float = Field(ge=0)
    remaining_runs: int = Field(ge=0)
    remaining_tokens: int = Field(ge=0)


class AdminOptimizationResponse(BaseModel):
    period_start: datetime
    plan: str
    usage: dict[str, int]
    cost_usd: float = Field(ge=0)
    successful_work_items: int = Field(ge=0)
    cost_per_successful_work_item_usd: float = Field(ge=0)
    budget: AdminOptimizationBudget
    optimization_actions: list[str]
