"""Platform-admin marketplace settlement and payout proposal responses."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    created_at: datetime
    updated_at: datetime
