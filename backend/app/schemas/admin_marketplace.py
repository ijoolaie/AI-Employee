"""Platform-admin marketplace settlement and payout proposal responses."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MarketplacePayoutApprovalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = "approve"
    reason: str | None = None


class MarketplacePayoutApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    proposal_id: UUID
    platform_admin_tenant_id: UUID
    decided_by_user_id: UUID
    status: str
    reason: str | None
    decided_at: datetime


class MarketplacePayoutProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    settlement_id: UUID
    seller_tenant_id: UUID
    platform_admin_tenant_id: UUID
    amount: Decimal
    currency: str
    provider: str
    status: str
    execution_status: str
    metadata: dict
    provider_payout_id: str | None = None
    executed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MarketplaceFinancialCurrencySummary(BaseModel):
    settlement_count: int
    gross_amount: str
    platform_fee_amount: str
    seller_net_amount: str


class MarketplaceFinancialSummaryResponse(BaseModel):
    verified_settlement_count: int
    verified_paid_purchase_count: int
    payout_proposal_count: int
    by_currency: dict[str, MarketplaceFinancialCurrencySummary]
    evidence_basis: str
    external_customer_revenue_verified: bool
    external_seller_payout_verified: bool
    execution_authority_changed: bool
