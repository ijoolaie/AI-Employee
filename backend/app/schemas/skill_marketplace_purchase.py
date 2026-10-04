from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SkillMarketplacePurchaseCreate(BaseModel):
    publication_id: UUID
    employee_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=255)


class SkillMarketplacePurchaseResponse(BaseModel):
    purchase_id: UUID
    deal_id: UUID
    status: str
    provider: str
    provider_execution: str
    executed: bool
    checkout_url: str | None
    provider_payment_id: str | None
    buyer_tenant_id: UUID
    seller_tenant_id: UUID
    employee_id: UUID
    skill_package_id: UUID
    product_id: UUID
    amount: str
    currency: str
    idempotent_replay: bool
