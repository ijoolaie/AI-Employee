"""W20 third-party Employee Marketplace package and installation ledgers."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, event, func, inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmployeeMarketplacePackageStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class EmployeeMarketplaceInstallationStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class EmployeeMarketplacePackage(Base):
    """Immutable marketplace snapshot of a published, evaluated AgentTemplate.

    The package is untrusted marketplace metadata. It never grants execution
    authority; installation creates a buyer-owned suspended template.
    """

    __tablename__ = "employee_marketplace_packages"
    __table_args__ = (
        UniqueConstraint("owner_tenant_id", "slug", "version", name="uq_employee_marketplace_pkg_owner_slug_version"),
        UniqueConstraint("owner_tenant_id", "id", name="uq_employee_marketplace_pkg_owner_id"),
        Index("ix_employee_marketplace_pkg_owner_status", "owner_tenant_id", "status"),
        Index("ix_employee_marketplace_pkg_visibility", "visibility"),
        ForeignKeyConstraint(
            ["owner_tenant_id", "source_agent_template_id"],
            ["agent_templates.tenant_id", "agent_templates.id"],
            name="fk_employee_marketplace_pkg_source_template_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_agent_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[EmployeeMarketplacePackageStatus] = mapped_column(
        Enum(
            EmployeeMarketplacePackageStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="employeemarketplacepackagestatus",
        ),
        nullable=False,
        default=EmployeeMarketplacePackageStatus.DRAFT,
    )
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="private")
    risk_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    employee_manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    permission_manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    skill_package_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    workflow_refs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    visual_pack: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmployeeMarketplaceInstallation(Base):
    """Buyer-scoped install ledger; execution remains a separate governed gate."""

    __tablename__ = "employee_marketplace_installations"
    __table_args__ = (
        UniqueConstraint("buyer_tenant_id", "package_id", name="uq_employee_marketplace_install_buyer_package"),
        Index("ix_employee_marketplace_install_buyer_status", "buyer_tenant_id", "status"),
        Index("ix_employee_marketplace_install_package", "package_id"),
        ForeignKeyConstraint(
            ["package_id"],
            ["employee_marketplace_packages.id"],
            name="fk_employee_marketplace_install_package",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["buyer_tenant_id", "imported_agent_template_id"],
            ["agent_templates.tenant_id", "agent_templates.id"],
            name="fk_employee_marketplace_install_template_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["buyer_tenant_id", "imported_agent_definition_id"],
            ["agent_definitions.tenant_id", "agent_definitions.id"],
            name="fk_employee_marketplace_install_definition_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["buyer_tenant_id"],
            ["tenants.id"],
            name="fk_employee_marketplace_install_buyer_tenant",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    imported_agent_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    imported_agent_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sponsor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[EmployeeMarketplaceInstallationStatus] = mapped_column(
        Enum(
            EmployeeMarketplaceInstallationStatus,
            values_callable=lambda cls: [item.value for item in cls],
            name="employeemarketplaceinstallationstatus",
        ),
        nullable=False,
        default=EmployeeMarketplaceInstallationStatus.ACTIVE,
    )
    provider_execution_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NOT_VERIFIED")
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


@event.listens_for(EmployeeMarketplacePackage, "before_update")
def _reject_published_package_update(mapper, connection, target) -> None:
    history = inspect(target).attrs.status.history
    committed_status = history.deleted[0] if history.deleted else None
    if committed_status == EmployeeMarketplacePackageStatus.PUBLISHED:
        raise ValueError("published employee marketplace package records are immutable")
