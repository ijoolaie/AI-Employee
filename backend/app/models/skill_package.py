"""Versioned, tenant-scoped skill packages; installation is non-authoritative metadata."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkillPackageStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class EmployeeSkillInstallationStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class SkillPackage(Base):
    """A versioned skill artifact; it never carries execution authority."""

    __tablename__ = "skill_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", "version", name="uq_skill_packages_tenant_slug_version"),
        UniqueConstraint("tenant_id", "id", name="uq_skill_packages_tenant_id_id"),
        Index("ix_skill_packages_tenant_status", "tenant_id", "status"),
        Index("ix_skill_packages_product", "tenant_id", "product_id"),
        ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_skill_packages_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            name="fk_skill_packages_product_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[SkillPackageStatus] = mapped_column(
        Enum(SkillPackageStatus, values_callable=lambda cls: [item.value for item in cls], name="skillpackagestatus"),
        nullable=False,
        default=SkillPackageStatus.DRAFT,
    )
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    compatibility: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    presentation_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmployeeSkillInstallation(Base):
    """Tenant-scoped installation ledger; never mutates permissions or allowed tools."""

    __tablename__ = "employee_skill_installations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_id", "skill_package_id", name="uq_employee_skill_installation"),
        Index("ix_employee_skill_installations_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_employee_skill_installations_tenant_status", "tenant_id", "status"),
        Index("ix_employee_skill_installations_source_owner", "source_owner_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_employee_skill_installations_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["employees.tenant_id", "employees.id"],
            name="fk_employee_skill_installations_employee_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["source_owner_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_employee_skill_installations_source_package_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_owner_tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    skill_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[EmployeeSkillInstallationStatus] = mapped_column(
        Enum(EmployeeSkillInstallationStatus, values_callable=lambda cls: [item.value for item in cls], name="employeeskillinstallationstatus"),
        nullable=False,
        default=EmployeeSkillInstallationStatus.ACTIVE,
    )
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
