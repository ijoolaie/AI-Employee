"""API contracts for World Mode one-time commerce."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated


ShortKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


class WorldCatalogueItemResponse(BaseModel):
    id: UUID
    code: str
    item_type: str
    name: str
    description: str | None
    price_options: dict
    is_free: bool
    model_config = ConfigDict(from_attributes=True)


class WorldOrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_code: ShortKey
    currency: str = Field(pattern="^(IRR|USD|USDT|WORLD_CREDIT)$")
    payment_method: str = Field(pattern="^(manual_transfer|gateway|crypto|world_credit)$")
    payment_provider: str = Field(min_length=1, max_length=64)
    idempotency_key: ShortKey


class WorldPaymentSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_transaction_ref: str = Field(min_length=1, max_length=255)


class WorldPaymentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=2000)


class WorldOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    buyer_user_id: UUID
    item_code_snapshot: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_provider: str
    provider_transaction_ref: str | None
    status: str
    payment_submitted_at: datetime | None
    approved_by_user_id: UUID | None
    approved_by_username: str | None
    approved_at: datetime | None
    activated_by_user_id: UUID | None
    activated_by_username: str | None
    activated_at: datetime | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldFeatureEntitlementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    item_code: str
    item_type: str
    source_order_id: UUID
    status: str
    activated_by_user_id: UUID | None
    activated_by_username: str | None
    activated_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldFeatureAccessResponse(BaseModel):
    item_code: str
    granted: bool
    access_source: str
    entitlement_id: UUID | None = None
    item_type: str | None = None


class WorldCommerceEventResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    order_id: UUID
    event_type: str
    actor_user_id: UUID | None
    actor_username: str | None
    from_status: str | None
    to_status: str | None
    details: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldSupportOrderSummary(BaseModel):
    id: UUID
    item_code_snapshot: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldSupportEntitlementSummary(BaseModel):
    item_code: str
    item_type: str
    status: str
    activated_at: datetime
    revoked_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class WorldSupportDiagnosticsResponse(BaseModel):
    tenant_id: UUID
    order_counts_by_status: dict[str, int]
    active_entitlement_count: int
    recent_orders: list[WorldSupportOrderSummary]
    entitlements: list[WorldSupportEntitlementSummary]
