"""Tenant-safe ownership operations for presentation-only cosmetics."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_order import BusinessOrder
from app.models.cosmetic_entitlement import CosmeticEntitlement
from app.models.employee import Employee
from app.models.product import Product
from app.services import audit_service


COSMETIC_TYPES = {"gender_presentation", "outfit", "hair_style", "accessory"}
COSMETIC_VALUES = {
    "gender_presentation": {"neutral", "feminine", "masculine"},
    "outfit": {"business", "casual", "technical", "formal"},
    "hair_style": {"default", "short", "long", "curly", "tied"},
    "accessory": {"none", "glasses", "headset", "badge"},
}
COSMETIC_PRODUCT_CATEGORY = "employee_cosmetic"


class CosmeticEntitlementError(ValueError):
    """Raised when cosmetic ownership invariants are violated."""


def _validate_cosmetic(cosmetic_type: str, cosmetic_value: str) -> None:
    if cosmetic_type not in COSMETIC_TYPES:
        raise CosmeticEntitlementError("cosmetic type is invalid")
    if cosmetic_value not in COSMETIC_VALUES[cosmetic_type]:
        raise CosmeticEntitlementError("cosmetic value is invalid")


def _validate_product_contract(product: Product, cosmetic_type: str, cosmetic_value: str) -> None:
    """Only explicitly designated cosmetic catalog products may create ownership."""
    if not product.is_active:
        raise CosmeticEntitlementError("product is inactive")
    if product.category != COSMETIC_PRODUCT_CATEGORY:
        raise CosmeticEntitlementError("product is not an employee cosmetic")
    attributes = product.attributes or {}
    if attributes.get("cosmetic_type") != cosmetic_type or attributes.get("cosmetic_value") != cosmetic_value:
        raise CosmeticEntitlementError("product cosmetic contract does not match entitlement")


async def grant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    product_id: uuid.UUID,
    cosmetic_type: str,
    cosmetic_value: str,
    actor_id: uuid.UUID | None = None,
    source_order_id: uuid.UUID | None = None,
) -> CosmeticEntitlement:
    _validate_cosmetic(cosmetic_type, cosmetic_value)

    employee = (
        await db.execute(
            select(Employee).where(Employee.id == employee_id, Employee.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if employee is None:
        raise CosmeticEntitlementError("employee not found in tenant")

    product = (
        await db.execute(
            select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if product is None:
        raise CosmeticEntitlementError("product not found in tenant")
    _validate_product_contract(product, cosmetic_type, cosmetic_value)

    if source_order_id is not None:
        order = (
            await db.execute(
                select(BusinessOrder).where(
                    BusinessOrder.id == source_order_id,
                    BusinessOrder.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if order is None:
            raise CosmeticEntitlementError("source order not found in tenant")

    existing = (
        await db.execute(
            select(CosmeticEntitlement).where(
                CosmeticEntitlement.tenant_id == tenant_id,
                CosmeticEntitlement.employee_id == employee_id,
                CosmeticEntitlement.product_id == product_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status == "active":
            raise CosmeticEntitlementError("cosmetic entitlement already exists")
        existing.status = "active"
        existing.revoked_at = None
        existing.cosmetic_type = cosmetic_type
        existing.cosmetic_value = cosmetic_value
        existing.source_order_id = source_order_id
        await db.flush()
        entitlement = existing
    else:
        entitlement = CosmeticEntitlement(
            tenant_id=tenant_id,
            employee_id=employee_id,
            product_id=product_id,
            cosmetic_type=cosmetic_type,
            cosmetic_value=cosmetic_value,
            status="active",
            source_order_id=source_order_id,
        )
        db.add(entitlement)
        await db.flush()

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="cosmetic_entitlement.granted",
        resource_type="cosmetic_entitlement",
        resource_id=str(entitlement.id),
        metadata={
            "employee_id": str(employee_id),
            "product_id": str(product_id),
            "cosmetic_type": cosmetic_type,
            "cosmetic_value": cosmetic_value,
            "source_order_id": str(source_order_id) if source_order_id else None,
            "presentation_only": True,
        },
    )
    return entitlement


async def list_for_employee(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    active_only: bool = True,
) -> list[CosmeticEntitlement]:
    stmt = select(CosmeticEntitlement).where(
        CosmeticEntitlement.tenant_id == tenant_id,
        CosmeticEntitlement.employee_id == employee_id,
    )
    if active_only:
        stmt = stmt.where(CosmeticEntitlement.status == "active")
    stmt = stmt.order_by(CosmeticEntitlement.created_at.desc(), CosmeticEntitlement.id.desc())
    return list((await db.execute(stmt)).scalars().all())


async def revoke(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entitlement_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
) -> CosmeticEntitlement:
    entitlement = (
        await db.execute(
            select(CosmeticEntitlement).where(
                CosmeticEntitlement.id == entitlement_id,
                CosmeticEntitlement.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if entitlement is None:
        raise CosmeticEntitlementError("cosmetic entitlement not found")
    if entitlement.status == "revoked":
        return entitlement

    entitlement.status = "revoked"
    entitlement.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="cosmetic_entitlement.revoked",
        resource_type="cosmetic_entitlement",
        resource_id=str(entitlement.id),
        metadata={"employee_id": str(entitlement.employee_id), "presentation_only": True},
    )
    return entitlement


async def assert_owned(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    product_id: uuid.UUID,
) -> CosmeticEntitlement:
    entitlement = (
        await db.execute(
            select(CosmeticEntitlement).where(
                CosmeticEntitlement.tenant_id == tenant_id,
                CosmeticEntitlement.employee_id == employee_id,
                CosmeticEntitlement.product_id == product_id,
                CosmeticEntitlement.status == "active",
            )
        )
    ).scalar_one_or_none()
    if entitlement is None:
        raise CosmeticEntitlementError("active cosmetic entitlement not found")
    return entitlement
