"""Pydantic schemas for Feedback endpoints (Phase 3 Validation tooling)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=4000)
    run_id: UUID | None = None
    employee_id: UUID | None = None
    category: str = Field(default="run", pattern="^(run|general)$")


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    run_id: UUID | None
    employee_id: UUID | None
    rating: int
    comment: str | None
    category: str
    created_at: datetime


class ValidationTenantSummary(BaseModel):
    tenant_id: UUID
    tenant_name: str
    report_employee_runs_last_14d: int
    report_employee_runs_total: int
    last_run_at: datetime | None
    feedback_count: int
    avg_rating: float | None


class ValidationSummaryResponse(BaseModel):
    active_tenant_count: int
    meets_phase3_customer_criteria: bool
    phase3_customer_target: int = 3
    total_feedback_count: int
    overall_avg_rating: float | None
    tenants: list[ValidationTenantSummary]
    recent_feedback: list[FeedbackResponse]
