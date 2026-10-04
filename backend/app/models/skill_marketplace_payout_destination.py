"""Tenant-scoped seller payout destination bindings.

A destination is an opaque provider-owned reference, never a bank credential,
payment secret, or arbitrary URL. Binding a destination does not execute a
payout.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplacePayoutDestinationStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class SkillMarketplacePayoutDestination(Base):
    """Historical, tenant-scoped destination binding for seller payouts."""

    __tablename__ = "skill_marketplace_payout_destinations"
    __table_args__ = (
        Index(
            "uq_skill_marketplace_payout_destination_active_seller",
            "seller_tenant_id",
            unique=True,
            postgresql_where=__import__("sqlalchemy").text("status = 'active'"),
        ),
        Index(
            "ix_skill_marketplace_payout_destinations_seller",
            "seller_tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    seller_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    destination_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SkillMarketplacePayoutDestinationStatus] = mapped_column(
        Enum(
            SkillMarketplacePayoutDestinationStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepayoutdestinationstatus",
        ),
        nullable=False,
        default=SkillMarketplacePayoutDestinationStatus.ACTIVE,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revoked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
