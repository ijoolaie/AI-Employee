"""Separate human approval ledger for marketplace seller payouts."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplacePayoutApprovalStatus(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class SkillMarketplacePayoutApproval(Base):
    __tablename__ = "skill_marketplace_payout_approvals"
    __table_args__ = (
        UniqueConstraint("proposal_id", name="uq_skill_marketplace_payout_approval_proposal"),
        Index("ix_skill_marketplace_payout_approvals_admin", "platform_admin_tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_marketplace_payout_proposals.id", ondelete="RESTRICT"),
        nullable=False,
    )
    platform_admin_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    decided_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[SkillMarketplacePayoutApprovalStatus] = mapped_column(
        Enum(
            SkillMarketplacePayoutApprovalStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepayoutapprovalstatus",
        ),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(2000))
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
