"""Tenant-local installation binding for an Agent Team version."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TeamInstallation(Base):
    """Authorized tenant-local binding to an immutable TeamVersion.

    Marketplace imports create a tenant-local TeamDefinition/TeamVersion copy
    and retain the publication identity here for provenance and idempotency.
    """

    __tablename__ = "team_installations"
    __table_args__ = (
        Index(
            "uq_team_installations_tenant_version_workspace_null",
            "tenant_id", "team_version_id",
            unique=True,
            postgresql_where=text("workspace_key IS NULL"),
        ),
        Index(
            "uq_team_installations_tenant_version_workspace",
            "tenant_id", "team_version_id", "workspace_key",
            unique=True,
            postgresql_where=text("workspace_key IS NOT NULL"),
        ),
        Index(
            "uq_team_installations_tenant_publication_workspace_null",
            "tenant_id", "source_publication_id",
            unique=True,
            postgresql_where=text("source_publication_id IS NOT NULL AND workspace_key IS NULL"),
        ),
        Index(
            "uq_team_installations_tenant_publication_workspace",
            "tenant_id", "source_publication_id", "workspace_key",
            unique=True,
            postgresql_where=text("source_publication_id IS NOT NULL AND workspace_key IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("team_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_publications.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    workspace_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    installed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team_version: Mapped["TeamVersion"] = relationship()


from app.models.team_version import TeamVersion  # noqa: E402
