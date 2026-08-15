"""Schemas for sales deals (Phase 9)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BusinessDealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: str | None = None
    stage: str = Field(default="lead", pattern="^(lead|qualified|proposal|negotiation|won|lost)$")
    amount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="IRR", min_length=3, max_length=8)
    probability: int = Field(default=10, ge=0, le=100)
    expected_close_date: date | None = None
    owner_name: str | None = None
    notes: str | None = None
    source: str | None = None
    order_id: UUID | None = None


class BusinessDealStageUpdate(BaseModel):
    stage: str = Field(pattern="^(lead|qualified|proposal|negotiation|won|lost)$")
    probability: int | None = Field(default=None, ge=0, le=100)


class BusinessDealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    customer_name: str
    customer_email: str | None
    stage: str
    amount: Decimal
    currency: str
    probability: int
    expected_close_date: date | None
    owner_name: str | None
    notes: str | None
    source: str | None
    order_id: UUID | None
    created_at: datetime
    updated_at: datetime


class SalesPipelineSummary(BaseModel):
    counts_by_stage: dict[str, int]
    amount_by_stage: dict[str, float]
    weighted_pipeline: float
    won_amount: float
    lost_amount: float
    open_deals: int
    total_deals: int
    currency: str


class SalesForecast(BaseModel):
    method: str
    horizon_days: int
    expected_revenue: float
    currency: str
    assumptions: dict
