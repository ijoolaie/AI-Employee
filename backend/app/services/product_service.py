import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product

async def list_products(db: AsyncSession, tenant_id: uuid.UUID, query: str | None = None, active_only: bool = False):
    stmt = select(Product).where(Product.tenant_id == tenant_id).order_by(Product.created_at.desc())
    if active_only: stmt = stmt.where(Product.is_active.is_(True))
    if query:
        like = f"%{query}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.category.ilike(like)))
    return list((await db.execute(stmt)).scalars().all())

async def create_product(db: AsyncSession, tenant_id: uuid.UUID, payload: dict):
    product = Product(tenant_id=tenant_id, **payload)
    db.add(product); await db.flush(); await db.refresh(product)
    return product

async def update_inventory(db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID, inventory: int):
    product = (await db.execute(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))).scalar_one_or_none()
    if not product: return None
    product.inventory = inventory
    await db.flush(); await db.refresh(product)
    return product
