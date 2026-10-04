"""Governed W16 skill package catalog and installation ledger."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ConflictError, NotFoundError, ValidationAppError
from app.models.employee import Employee
from app.models.product import Product
from app.models.skill_package import (
    EmployeeSkillInstallation,
    EmployeeSkillInstallationStatus,
    SkillPackage,
    SkillPackageStatus,
)
from app.services import audit_service

SKILL_PRODUCT_CATEGORY = "employee_skill"


class SkillMarketplaceError(AppError):
    """Raised when a skill marketplace invariant is violated."""

    def __init__(self, message: str):
        super().__init__("SKILL_MARKETPLACE_INVALID", message, 422)


EXECUTION_AUTHORITY_KEYS = frozenset({
    "allowed_tools",
    "permissions",
    "approval_policy",
    "capability_contract",
    "tool_bindings",
})


def _contains_execution_authority(value: object) -> bool:
    if isinstance(value, dict):
        if EXECUTION_AUTHORITY_KEYS.intersection(value):
            return True
        return any(_contains_execution_authority(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_execution_authority(item) for item in value)
    return False


def _validate_skill_metadata(value: object, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValidationAppError(f"{field_name} must be an object")
    if _contains_execution_authority(value):
        raise SkillMarketplaceError(f"{field_name} cannot declare execution authority")


def _validate_manifest(manifest: dict) -> None:
    _validate_skill_metadata(manifest, "skill manifest")


def _validate_product_contract(product: Product | None, package: SkillPackage) -> None:
    if package.product_id is None:
        return
    if product is None or not product.is_active:
        raise SkillMarketplaceError("skill product is unavailable")
    if product.category != SKILL_PRODUCT_CATEGORY:
        raise SkillMarketplaceError("product is not an employee skill")
    attributes = product.attributes or {}
    if attributes.get("skill_package_slug") != package.slug:
        raise SkillMarketplaceError("skill product does not match package")
    try:
        product_version = int(attributes.get("skill_package_version", -1))
    except (TypeError, ValueError):
        raise SkillMarketplaceError("skill product version is invalid") from None
    if product_version != package.version:
        raise SkillMarketplaceError("skill product version does not match package")


async def create_package(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    slug: str,
    name: str,
    version: int = 1,
    description: str | None = None,
    manifest: dict | None = None,
    compatibility: dict | None = None,
    presentation_metadata: dict | None = None,
    product_id: uuid.UUID | None = None,
) -> SkillPackage:
    if not slug.strip() or len(slug) > 120:
        raise ValidationAppError("skill slug is invalid")
    if version < 1:
        raise ValidationAppError("skill version must be at least 1")
    manifest = {} if manifest is None else manifest
    compatibility = {} if compatibility is None else compatibility
    presentation_metadata = {} if presentation_metadata is None else presentation_metadata
    _validate_manifest(manifest)
    _validate_skill_metadata(compatibility, "skill compatibility")
    _validate_skill_metadata(presentation_metadata, "skill presentation metadata")
    duplicate = (await db.execute(select(SkillPackage).where(
        SkillPackage.tenant_id == tenant_id,
        SkillPackage.slug == slug,
        SkillPackage.version == version,
    ))).scalar_one_or_none()
    if duplicate:
        raise ConflictError("skill package version already exists")

    product = None
    if product_id is not None:
        product = (await db.execute(select(Product).where(
            Product.id == product_id, Product.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if product is None:
            raise NotFoundError("skill product not found")
    package = SkillPackage(
        tenant_id=tenant_id,
        product_id=product_id,
        slug=slug,
        name=name,
        description=description,
        version=version,
        manifest=manifest,
        compatibility=compatibility,
        presentation_metadata=presentation_metadata,
        status=SkillPackageStatus.DRAFT,
    )
    _validate_product_contract(product, package)
    db.add(package)
    await db.flush()
    await db.refresh(package)
    return package


async def publish_package(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    package_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> SkillPackage:
    package = (await db.execute(select(SkillPackage).where(
        SkillPackage.id == package_id, SkillPackage.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if package is None:
        raise NotFoundError("skill package not found")
    if package.status not in {SkillPackageStatus.DRAFT, SkillPackageStatus.SUSPENDED}:
        raise ConflictError("skill package is not publishable")
    _validate_manifest(package.manifest or {})
    _validate_skill_metadata(package.compatibility or {}, "skill compatibility")
    _validate_skill_metadata(package.presentation_metadata or {}, "skill presentation metadata")
    product = None
    if package.product_id:
        product = (await db.execute(select(Product).where(
            Product.id == package.product_id, Product.tenant_id == tenant_id,
        ))).scalar_one_or_none()
    _validate_product_contract(product, package)
    package.status = SkillPackageStatus.PUBLISHED
    package.published_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="skill_package.published",
        resource_type="skill_package",
        resource_id=str(package.id),
        metadata={"slug": package.slug, "version": package.version, "presentation_only": True},
    )
    return package


async def install(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    skill_package_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    source_publication_id: uuid.UUID | None = None,
) -> EmployeeSkillInstallation:
    employee = (await db.execute(select(Employee).where(
        Employee.id == employee_id, Employee.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("employee not found in tenant")

    source_owner_tenant_id = tenant_id
    if source_publication_id is not None:
        from app.models.skill_marketplace_publication import SkillMarketplacePublication
        publication = (await db.execute(select(SkillMarketplacePublication).where(
            SkillMarketplacePublication.id == source_publication_id,
            SkillMarketplacePublication.visibility == "public",
        ))).scalar_one_or_none()
        if publication is None:
            raise NotFoundError("public skill marketplace publication not found")
        if publication.skill_package_id != skill_package_id:
            raise ConflictError("skill package does not match marketplace publication")
        source_owner_tenant_id = publication.owner_tenant_id
        if source_owner_tenant_id == tenant_id:
            raise ConflictError("marketplace publication owner cannot be the buyer tenant")

    package = (await db.execute(select(SkillPackage).where(
        SkillPackage.id == skill_package_id,
        SkillPackage.tenant_id == source_owner_tenant_id,
        SkillPackage.status == SkillPackageStatus.PUBLISHED,
    ))).scalar_one_or_none()
    if package is None:
        raise NotFoundError("published skill package not found")

    _validate_manifest(package.manifest or {})
    _validate_skill_metadata(package.compatibility or {}, "skill compatibility")
    _validate_skill_metadata(package.presentation_metadata or {}, "skill presentation metadata")
    if package.product_id is not None:
        from app.services.skill_purchase_entitlement_service import assert_owned
        try:
            await assert_owned(
                db,
                tenant_id=tenant_id,
                employee_id=employee_id,
                skill_package_id=skill_package_id,
            )
        except ConflictError as exc:
            raise SkillMarketplaceError(str(exc)) from exc

    existing = (await db.execute(select(EmployeeSkillInstallation).where(
        EmployeeSkillInstallation.tenant_id == tenant_id,
        EmployeeSkillInstallation.employee_id == employee_id,
        EmployeeSkillInstallation.skill_package_id == skill_package_id,
    ))).scalar_one_or_none()
    if existing:
        if existing.status == EmployeeSkillInstallationStatus.ACTIVE:
            raise ConflictError("skill package is already installed")
        existing.status = EmployeeSkillInstallationStatus.ACTIVE
        existing.installed_at = datetime.now(timezone.utc)
        existing.revoked_at = None
        existing.source_owner_tenant_id = source_owner_tenant_id
        installation = existing
    else:
        installation = EmployeeSkillInstallation(
            tenant_id=tenant_id,
            employee_id=employee_id,
            source_owner_tenant_id=source_owner_tenant_id,
            skill_package_id=skill_package_id,
            status=EmployeeSkillInstallationStatus.ACTIVE,
        )
        try:
            async with db.begin_nested():
                db.add(installation)
                await db.flush()
        except IntegrityError as exc:
            constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if constraint_name == "uq_employee_skill_installation":
                raise ConflictError("skill package is already installed") from exc
            raise
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="employee_skill.installed",
        resource_type="employee_skill_installation",
        resource_id=str(installation.id),
        metadata={
            "employee_id": str(employee_id),
            "skill_package_id": str(skill_package_id),
            "source_owner_tenant_id": str(source_owner_tenant_id),
            "source_publication_id": str(source_publication_id) if source_publication_id else None,
            "skill_slug": package.slug,
            "skill_version": package.version,
            "presentation_only": True,
            "execution_authority_changed": False,
            "permissions_changed": False,
            "allowed_tools_changed": False,
        },
    )
    return installation

async def revoke(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    skill_package_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
) -> EmployeeSkillInstallation:
    employee = (await db.execute(select(Employee).where(
        Employee.id == employee_id, Employee.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("employee not found in tenant")

    installation = (await db.execute(select(EmployeeSkillInstallation).where(
EmployeeSkillInstallation.tenant_id == tenant_id,
        EmployeeSkillInstallation.employee_id == employee_id,
        EmployeeSkillInstallation.skill_package_id == skill_package_id,
        EmployeeSkillInstallation.status == EmployeeSkillInstallationStatus.ACTIVE,
    ))).scalar_one_or_none()
    if installation is None:
        raise NotFoundError("active skill installation not found")

    installation.status = EmployeeSkillInstallationStatus.REVOKED
    installation.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="employee_skill.revoked",
        resource_type="employee_skill_installation",
        resource_id=str(installation.id),
        metadata={
            "employee_id": str(employee_id),
            "skill_package_id": str(skill_package_id),
            "presentation_only": True,
            "execution_authority_changed": False,
            "permissions_changed": False,
            "allowed_tools_changed": False,
        },
    )
    return installation

async def list_for_employee(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    active_only: bool = True,
) -> list[EmployeeSkillInstallation]:
    employee = (await db.execute(select(Employee).where(
        Employee.id == employee_id, Employee.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("employee not found in tenant")

    stmt = select(EmployeeSkillInstallation).where(
        EmployeeSkillInstallation.tenant_id == tenant_id,
        EmployeeSkillInstallation.employee_id == employee_id,
    )
    if active_only:
        stmt = stmt.where(EmployeeSkillInstallation.status == EmployeeSkillInstallationStatus.ACTIVE)
    stmt = stmt.order_by(EmployeeSkillInstallation.installed_at.desc(), EmployeeSkillInstallation.id.desc())
    return list((await db.execute(stmt)).scalars().all())
