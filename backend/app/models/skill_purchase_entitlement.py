"""Tenant-scoped verified purchase entitlements for employee skills."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

import enum


class SkillPurchaseEntitlementStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class SkillPurchaseEntitlement(Base):
    """Verified commercial ownership; never grants execution authority."""

    __tablename__ = "skill_purchase_entitlements"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "employee_id", "skill_package_id",
            name="uq_skill_purchase_entitlement",
        ),
        UniqueConstraint(
            "provider", "provider_event_id",
            name="uq_skill_purchase_entitlement_provider_event",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["employees.tenant_id", "employees.id"],
            name="fk_skill_purchase_entitlement_employee_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["source_owner_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_skill_purchase_entitlement_source_package_tenant",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_skill_purchase_entitlements_tenant_employee",
            "tenant_id", "employee_id",
        ),
        Index(
            "ix_skill_purchase_entitlements_tenant_status",
            "tenant_id", "status",
        ),
        Index(
            "ix_skill_purchase_entitlements_source_owner",
            "source_owner_tenant_id",
        ),
        Index(
            "ix_skill_purchase_entitlements_source_publication",
            "source_publication_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_owner_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    skill_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_packages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_marketplace_publications.id", ondelete="RESTRICT"), nullable=True
    )
    source_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SkillPurchaseEntitlementStatus] = mapped_column(
        Enum(
            SkillPurchaseEntitlementStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="skillpurchaseentitlementstatus",
        ),
        nullable=False,
        default=SkillPurchaseEntitlementStatus.ACTIVE,
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
