"""Tenant model — root of multi-tenancy and commercial edition hierarchy."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    # active | suspended | trial
    tenant_kind: Mapped[str] = mapped_column(String(20), default="customer", nullable=False, index=True)
    # vendor | reseller | customer
    parent_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    vendor_release_tag: Mapped[str | None] = mapped_column(String(80))
    delivery_revision: Mapped[str | None] = mapped_column(String(120))
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")  # noqa: F821
    parent: Mapped["Tenant | None"] = relationship(
        "Tenant", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Tenant"]] = relationship("Tenant", back_populates="parent")
