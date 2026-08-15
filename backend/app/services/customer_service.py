import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.core.exceptions import NotFoundError

async def upsert_customer(db: AsyncSession, *, tenant_id: uuid.UUID, external_key: str, name=None, email=None, phone=None, channel=None) -> Customer:
    customer = (await db.execute(select(Customer).where(Customer.tenant_id == tenant_id, Customer.external_key == external_key))).scalar_one_or_none()
    if not customer:
        customer = Customer(tenant_id=tenant_id, external_key=external_key, name=name, email=email, phone=phone, last_channel=channel)
        db.add(customer)
    else:
        if name: customer.name = name
        if email: customer.email = email
        if phone: customer.phone = phone
        if channel: customer.last_channel = channel
    await db.flush(); await db.refresh(customer)
    return customer

async def list_customers(db: AsyncSession, *, tenant_id: uuid.UUID, q: str | None = None):
    stmt = select(Customer).where(Customer.tenant_id == tenant_id).order_by(Customer.updated_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Customer.name.ilike(like), Customer.email.ilike(like), Customer.phone.ilike(like), Customer.external_key.ilike(like)))
    return list((await db.execute(stmt.limit(200))).scalars().all())

async def get_customer(db: AsyncSession, *, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    customer = (await db.execute(select(Customer).where(Customer.tenant_id == tenant_id, Customer.id == customer_id))).scalar_one_or_none()
    if not customer: raise NotFoundError("Customer not found")
    return customer

async def update_customer(db: AsyncSession, *, tenant_id: uuid.UUID, customer_id: uuid.UUID, **data):
    customer = await get_customer(db, tenant_id=tenant_id, customer_id=customer_id)
    for k, v in data.items():
        if v is not None: setattr(customer, k, v)
    await db.flush(); await db.refresh(customer)
    return customer
