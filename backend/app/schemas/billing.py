from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class PlanResponse(BaseModel):
    code: str
    name: str
    monthly_price_usd: Decimal
    monthly_runs: int
    monthly_tokens: int
    max_employees: int
    max_workflows: int
    features: dict

class SubscriptionResponse(BaseModel):
    id: str
    plan: PlanResponse
    status: str
    provider: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: datetime | None
    trial_ends_at: datetime | None

class SubscribeRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=40)

class CancelRequest(BaseModel):
    at_period_end: bool = True

class BillingEventRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=40)
    provider_event_id: str = Field(min_length=1, max_length=255)
    event_type: str = Field(min_length=2, max_length=100)
    tenant_id: str | None = None
    plan_code: str | None = None
    status: str | None = None
    payload: dict = {}

class CheckoutSessionRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=40)

class CheckoutSessionResponse(BaseModel):
    checkout_url: str

class PortalSessionResponse(BaseModel):
    portal_url: str
