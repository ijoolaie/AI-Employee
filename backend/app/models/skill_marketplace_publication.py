"""Immutable marketplace publication records for third-party SkillPackage discovery."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillMarketplacePublication(Base):
    """Immutable discovery metadata; publication is not installation or execution authority."""

    __tablename__ = "skill_marketplace_publications"
    __table_args__ = (
        UniqueConstraint("skill_package_id", name="uq_skill_marketplace_publications_skill_package"),
        Index("ix_skill_marketplace_publications_owner_tenant", "owner_tenant_id"),
        Index("ix_skill_marketplace_publications_visibility", "visibility"),
        ForeignKeyConstraint(
            ["owner_tenant_id"],
            ["tenants.id"],
            name="fk_skill_marketplace_publications_owner_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["owner_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_skill_marketplace_publications_package_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    skill_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="private")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


@event.listens_for(SkillMarketplacePublication, "before_update")
def _reject_publication_update(mapper, connection, target) -> None:
    raise ValueError("skill marketplace publication records are immutable")
