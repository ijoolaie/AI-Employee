"""Platform-controlled marketplace payout proposals; no money transfer is executed."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplacePayoutProposalStatus(str, enum.Enum):
    PROPOSED = "proposed"
    CANCELLED = "cancelled"


class SkillMarketplacePayoutExecutionStatus(str, enum.Enum):
    NOT_EXECUTED = "not_executed"
    PENDING = "pending"
    ACCEPTED = "accepted"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SkillMarketplacePayoutProposal(Base):
    """Seller-net payout proposal with an immutable destination snapshot."""

    __tablename__ = "skill_marketplace_payout_proposals"
    __table_args__ = (
        UniqueConstraint(
            "settlement_id",
            name="uq_skill_marketplace_payout_proposal_settlement",
        ),
        Index(
            "ix_skill_marketplace_payout_proposals_seller",
            "seller_tenant_id",
        ),
        Index(
            "ix_skill_marketplace_payout_proposals_status",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_marketplace_settlements.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seller_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    platform_admin_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_marketplace_payout_destinations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    destination_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    destination_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="none")
    status: Mapped[SkillMarketplacePayoutProposalStatus] = mapped_column(
        Enum(
            SkillMarketplacePayoutProposalStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepayoutproposalstatus",
        ),
        nullable=False,
        default=SkillMarketplacePayoutProposalStatus.PROPOSED,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    provider_payout_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retryable: Mapped[bool] = mapped_column(default=False, nullable=False)
    executed: Mapped[bool] = mapped_column(default=False, nullable=False)
    external_execution: Mapped[bool] = mapped_column(default=False, nullable=False)
    reconciliation_evidence_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reconciliation_outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reconciled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_status: Mapped[SkillMarketplacePayoutExecutionStatus] = mapped_column(
        Enum(
            SkillMarketplacePayoutExecutionStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepayoutexecutionstatus",
        ),
        nullable=False,
        default=SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
