"""Tenant-scoped ownership of presentation-only employee cosmetics."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CosmeticEntitlement(Base):
    """An owned cosmetic; ownership never grants runtime authority."""

    __tablename__ = "cosmetic_entitlements"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "employee_id",
            "product_id",
            name="uq_cosmetic_entitlement_tenant_employee_product",
        ),
        Index("ix_cosmetic_entitlements_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_cosmetic_entitlements_tenant_status", "tenant_id", "status"),
        CheckConstraint(
            "cosmetic_type IN ('gender_presentation', 'outfit', 'hair_style', 'accessory')",
            name="ck_cosmetic_entitlement_type",
        ),
        CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_cosmetic_entitlement_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cosmetic_type: Mapped[str] = mapped_column(String(32), nullable=False)
    cosmetic_value: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    source_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
