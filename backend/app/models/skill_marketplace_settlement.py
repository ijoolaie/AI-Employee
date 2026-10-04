"""Verified marketplace financial allocation ledger.

This record accounts for gross payment, platform commission and seller net.
It does not execute a seller payout and does not calculate tax.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplaceSettlementStatus(str, enum.Enum):
    RECORDED = "recorded"


class SkillMarketplacePayoutStatus(str, enum.Enum):
    NOT_EXECUTED = "not_executed"
    EXECUTED = "executed"
    UNKNOWN = "unknown"


class SkillMarketplaceSettlement(Base):
    """One verified-payment allocation snapshot for a marketplace purchase."""

    __tablename__ = "skill_marketplace_settlements"
    __table_args__ = (
        UniqueConstraint(
            "purchase_id",
            name="uq_skill_marketplace_settlement_purchase",
        ),
        UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_skill_marketplace_settlement_provider_event",
        ),
        Index(
            "ix_skill_marketplace_settlements_buyer",
            "buyer_tenant_id",
        ),
        Index(
            "ix_skill_marketplace_settlements_seller",
            "seller_tenant_id",
        ),
        Index(
            "ix_skill_marketplace_settlements_status",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_marketplace_purchases.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revenue_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workforce_revenue_events.id", ondelete="RESTRICT"),
        nullable=False,
    )
    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seller_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    platform_fee_bps: Mapped[int] = mapped_column(nullable=False)
    platform_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    seller_net_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[SkillMarketplaceSettlementStatus] = mapped_column(
        Enum(
            SkillMarketplaceSettlementStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacesettlementstatus",
        ),
        nullable=False,
        default=SkillMarketplaceSettlementStatus.RECORDED,
    )
    payout_status: Mapped[SkillMarketplacePayoutStatus] = mapped_column(
        Enum(
            SkillMarketplacePayoutStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepayoutstatus",
        ),
        nullable=False,
        default=SkillMarketplacePayoutStatus.NOT_EXECUTED,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
