"""Buyer-side cross-tenant Skill Marketplace purchase commitments."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplacePurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class SkillMarketplacePurchase(Base):
    __tablename__ = "skill_marketplace_purchases"
    __table_args__ = (
        UniqueConstraint(
            "buyer_tenant_id", "idempotency_key",
            name="uq_skill_marketplace_purchase_buyer_idempotency",
        ),
        ForeignKeyConstraint(
            ["buyer_tenant_id", "employee_id"],
            ["employees.tenant_id", "employees.id"],
            name="fk_skill_marketplace_purchase_buyer_employee_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["seller_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_skill_marketplace_purchase_seller_package_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["seller_tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            name="fk_skill_marketplace_purchase_seller_product_tenant",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_skill_marketplace_purchases_buyer_status",
            "buyer_tenant_id", "status",
        ),
        Index(
            "ix_skill_marketplace_purchases_seller",
            "seller_tenant_id",
        ),
        Index(
            "ix_skill_marketplace_purchases_publication",
            "publication_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_marketplace_publications.id", ondelete="RESTRICT"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    skill_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    business_deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_deals.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(40))
    provider_event_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[SkillMarketplacePurchaseStatus] = mapped_column(
        Enum(
            SkillMarketplacePurchaseStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillmarketplacepurchasestatus",
        ),
        nullable=False,
        default=SkillMarketplacePurchaseStatus.PENDING,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
