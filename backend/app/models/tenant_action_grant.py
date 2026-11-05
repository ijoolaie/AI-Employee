"""Explicit, user-bound grants for Vendor/Reseller control-plane actions."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TenantActionGrant(Base):
    __tablename__ = "tenant_action_grants"
    __table_args__ = (
        CheckConstraint("length(trim(reason)) > 0", name="ck_tenant_action_grant_reason"),
        CheckConstraint("expires_at > created_at", name="ck_tenant_action_grant_expiry"),
        CheckConstraint(
            "action_code IN ('vendor.tenant.read','vendor.reseller.read','vendor.reseller.create','vendor.reseller.manage','vendor.customer.read','vendor.customer.create','vendor.customer.manage','reseller.customer.create','reseller.customer.read','reseller.customer.manage','reseller.entitlement.delegate')",
            name="ck_tenant_action_grant_action_code",
        ),
        Index(
            "uq_tenant_action_grant_active",
            "user_id",
            "tenant_id",
            "action_code",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index("ix_tenant_action_grants_tenant_user", "tenant_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)
    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
