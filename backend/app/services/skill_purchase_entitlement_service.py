"""Tenant-safe verified purchase ownership for commercial W16 skills."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.business_order import BusinessOrder
from app.models.employee import Employee
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.models.skill_purchase_entitlement import (
    SkillPurchaseEntitlement,
    SkillPurchaseEntitlementStatus,
)
from app.models.product import Product
from app.services import audit_service


async def grant_from_verified_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    deal,
    source_order_id: uuid.UUID,
    provider: str,
    provider_event_id: str,
) -> SkillPurchaseEntitlement | None:
    """Grant ownership only from a verified provider payment settlement."""
    metadata = deal.metadata_ or {}
    purchase = metadata.get("skill_purchase")
    marketplace = metadata.get("skill_marketplace_purchase")
    if not purchase:
        return None
    if metadata.get("skill_entitlement_granted") is True:
        return None

    required = {"employee_id", "product_id", "skill_package_id"}
    if set(purchase) != required:
        raise ConflictError("skill purchase contract is malformed")

    try:
        employee_id = uuid.UUID(str(purchase["employee_id"]))
        product_id = uuid.UUID(str(purchase["product_id"]))
        skill_package_id = uuid.UUID(str(purchase["skill_package_id"]))
    except (TypeError, ValueError) as exc:
        raise ConflictError("skill purchase contract contains invalid UUIDs") from exc

    order = (
        await db.execute(
            select(BusinessOrder).where(
                BusinessOrder.id == source_order_id,
                BusinessOrder.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if order is None:
        raise NotFoundError("verified skill purchase source order not found")

    employee = (
        await db.execute(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.tenant_id == tenant_id,
                Employee.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("skill purchase employee not found in tenant")

    source_owner_tenant_id = tenant_id
    source_publication_id = None
    if marketplace is not None:
        required_marketplace = {
            "buyer_tenant_id",
            "seller_tenant_id",
            "publication_id",
            "employee_id",
            "product_id",
            "skill_package_id",
            "skill_package_slug",
            "skill_package_version",
            "idempotency_key",
        }
        if set(marketplace) != required_marketplace:
            raise ConflictError("skill marketplace purchase contract is malformed")
        if str(marketplace["buyer_tenant_id"]) != str(tenant_id):
            raise ConflictError("skill marketplace buyer tenant does not match payment tenant")
        try:
            seller_tenant_id = uuid.UUID(str(marketplace["seller_tenant_id"]))
            source_publication_id = uuid.UUID(str(marketplace["publication_id"]))
        except (TypeError, ValueError) as exc:
            raise ConflictError("skill marketplace seller/publication identifiers are invalid") from exc
        source_owner_tenant_id = seller_tenant_id
        from app.models.skill_marketplace_publication import SkillMarketplacePublication
        publication = (
            await db.execute(
                select(SkillMarketplacePublication).where(
                    SkillMarketplacePublication.id == source_publication_id,
                    SkillMarketplacePublication.owner_tenant_id == seller_tenant_id,
                    SkillMarketplacePublication.skill_package_id == skill_package_id,
                    SkillMarketplacePublication.visibility == "public",
                )
            )
        ).scalar_one_or_none()
        if publication is None:
            raise NotFoundError("verified skill marketplace publication not found")

    package = (
        await db.execute(
            select(SkillPackage).where(
                SkillPackage.id == skill_package_id,
                SkillPackage.tenant_id == source_owner_tenant_id,
                SkillPackage.status == SkillPackageStatus.PUBLISHED,
            )
        )
    ).scalar_one_or_none()
    if package is None:
        raise NotFoundError("skill purchase package not found or unpublished")

    product = (
        await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == source_owner_tenant_id,
                Product.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if product is None:
        raise NotFoundError("skill purchase product not found or inactive")
    if package.product_id != product.id or product.category != "employee_skill":
        raise ConflictError("skill purchase product does not match package")
    attributes = product.attributes or {}
    if attributes.get("skill_package_slug") != package.slug:
        raise ConflictError("skill purchase product slug does not match package")
    try:
        product_version = int(attributes.get("skill_package_version", -1))
    except (TypeError, ValueError):
        raise ConflictError("skill purchase product version is invalid") from None
    if product_version != package.version:
        raise ConflictError("skill purchase product version does not match package")

    existing = (
        await db.execute(
            select(SkillPurchaseEntitlement).where(
                SkillPurchaseEntitlement.tenant_id == tenant_id,
                SkillPurchaseEntitlement.employee_id == employee_id,
                SkillPurchaseEntitlement.skill_package_id == skill_package_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status == SkillPurchaseEntitlementStatus.ACTIVE:
            raise ConflictError("skill purchase entitlement already exists")
        existing.status = SkillPurchaseEntitlementStatus.ACTIVE
        existing.granted_at = datetime.now(timezone.utc)
        existing.revoked_at = None
        existing.source_owner_tenant_id = source_owner_tenant_id
        existing.source_publication_id = source_publication_id
        existing.source_order_id = source_order_id
        existing.provider = provider
        existing.provider_event_id = provider_event_id
        entitlement = existing
    else:
        entitlement = SkillPurchaseEntitlement(
            tenant_id=tenant_id,
            employee_id=employee_id,
            source_owner_tenant_id=source_owner_tenant_id,
            source_publication_id=source_publication_id,
            skill_package_id=skill_package_id,
            source_order_id=source_order_id,
            provider=provider,
            provider_event_id=provider_event_id,
            status=SkillPurchaseEntitlementStatus.ACTIVE,
            metadata_={
                "presentation_only": True,
                "execution_authority_changed": False,
                "cross_tenant_marketplace": marketplace is not None,
            },
        )
        db.add(entitlement)
        await db.flush()

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=None,
        action="skill_purchase_entitlement.granted",
        resource_type="skill_purchase_entitlement",
        resource_id=str(entitlement.id),
        metadata={
            "employee_id": str(employee_id),
            "source_owner_tenant_id": str(source_owner_tenant_id),
            "source_publication_id": str(source_publication_id) if source_publication_id else None,
            "skill_package_id": str(skill_package_id),
            "product_id": str(product_id),
            "source_order_id": str(source_order_id),
            "provider": provider,
            "provider_event_id": provider_event_id,
            "cross_tenant_marketplace": marketplace is not None,
            "presentation_only": True,
            "execution_authority_changed": False,
            "permissions_changed": False,
            "allowed_tools_changed": False,
        },
    )
    deal_metadata = dict(metadata)
    deal_metadata["skill_entitlement_granted"] = True
    deal_metadata["skill_entitlement_id"] = str(entitlement.id)
    deal.metadata_ = deal_metadata
    await db.flush()
    return entitlement


async def assert_owned(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    skill_package_id: uuid.UUID,
) -> SkillPurchaseEntitlement:
    entitlement = (
        await db.execute(
            select(SkillPurchaseEntitlement).where(
                SkillPurchaseEntitlement.tenant_id == tenant_id,
                SkillPurchaseEntitlement.employee_id == employee_id,
                SkillPurchaseEntitlement.skill_package_id == skill_package_id,
                SkillPurchaseEntitlement.status == SkillPurchaseEntitlementStatus.ACTIVE,
            )
        )
    ).scalar_one_or_none()
    if entitlement is None:
        raise ConflictError("verified skill purchase entitlement is missing or revoked")
    return entitlement
