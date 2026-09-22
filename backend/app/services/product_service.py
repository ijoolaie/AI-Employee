import uuid

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.product import Product


PRODUCT_SKU_INDEX_NAME = "uq_products_tenant_normalized_sku"


def normalize_sku(sku: str | None) -> str | None:
    """Normalize optional SKU values to a stable tenant-scoped identity."""
    if sku is None:
        return None
    normalized = sku.strip().upper()
    return normalized or None


async def list_products(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str | None = None,
    active_only: bool = False,
):
    stmt = select(Product).where(Product.tenant_id == tenant_id).order_by(Product.created_at.desc())
    if active_only:
        stmt = stmt.where(Product.is_active.is_(True))
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(like),
                Product.sku.ilike(like),
                Product.category.ilike(like),
            )
        )
    return list((await db.execute(stmt)).scalars().all())


async def create_product(db: AsyncSession, tenant_id: uuid.UUID, payload: dict):
    data = dict(payload)
    data["sku"] = normalize_sku(data.get("sku"))

    try:
        async with db.begin_nested():
            product = Product(tenant_id=tenant_id, **data)
            db.add(product)
            await db.flush()
    except IntegrityError as exc:
        constraint_name = getattr(exc.orig, "constraint_name", None)
        if constraint_name != PRODUCT_SKU_INDEX_NAME:
            raise
        raise ConflictError("Product SKU already exists in this tenant") from exc

    await db.refresh(product)
    return product


async def update_inventory(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    inventory: int,
):
    product = (
        await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not product:
        return None
    product.inventory = inventory
    await db.flush()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: dict,
):
    product = (
        await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not product:
        return None

    data = dict(payload)
    if "sku" in data:
        data["sku"] = normalize_sku(data["sku"])
    for key, value in data.items():
        setattr(product, key, value)

    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError as exc:
        constraint_name = getattr(exc.orig, "constraint_name", None)
        if constraint_name != PRODUCT_SKU_INDEX_NAME:
            raise
        raise ConflictError("Product SKU already exists in this tenant") from exc

    await db.refresh(product)
    return product
