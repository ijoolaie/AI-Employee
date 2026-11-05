"""Explicit user-bound authorization to access a direct child tenant portal."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PortalAccessGrant(Base):
    __tablename__ = "portal_access_grants"
    __table_args__ = (
        Index(
            "uq_portal_access_grant_active",
            "actor_user_id",
            "target_tenant_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index("ix_portal_access_grants_actor_tenant", "actor_tenant_id"),
        Index("ix_portal_access_grants_target_tenant", "target_tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    target_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
