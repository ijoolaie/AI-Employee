import uuid
from app.core.exceptions import ConflictError

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.services import audit_service


CUSTOMER_EXTERNAL_KEY_INDEX_NAME = "uq_customers_tenant_external_key"


async def upsert_customer(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    external_key: str,
    name=None,
    email=None,
    phone=None,
    channel=None,
) -> Customer:
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.external_key == external_key,
            )
        )
    ).scalar_one_or_none()
    if not customer:
        candidate = Customer(
            tenant_id=tenant_id,
            external_key=external_key,
            name=name,
            email=email,
            phone=phone,
            last_channel=channel,
        )
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
        except IntegrityError:
            customer = (
                await db.execute(
                    select(Customer).where(
                        Customer.tenant_id == tenant_id,
                        Customer.external_key == external_key,
                    )
                )
            ).scalar_one_or_none()
            if customer is None:
                raise
        else:
            customer = candidate
    if customer:
        if name:
            customer.name = name
        if email:
            customer.email = email
        if phone:
            customer.phone = phone
        if channel:
            customer.last_channel = channel
    await db.flush()
    await db.refresh(customer)
    return customer


async def create_customer(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    external_key: str | None = None,
    name=None,
    email=None,
    phone=None,
    tags=None,
    notes=None,
) -> Customer:
    key = external_key or f"manual:{uuid.uuid4()}"
    existing = (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.external_key == key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Customer external key already exists")
    customer = Customer(
        tenant_id=tenant_id,
        external_key=key,
        name=name,
        email=email,
        phone=phone,
        tags=tags or [],
        notes=notes,
        is_active=True,
    )
    try:
        async with db.begin_nested():
            db.add(customer)
            await db.flush()
    except IntegrityError as exc:
        constraint_name = getattr(exc.orig, "constraint_name", None)
        if constraint_name == CUSTOMER_EXTERNAL_KEY_INDEX_NAME:
            raise ConflictError("Customer external key already exists") from exc
        raise
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="customer.created",
        resource_type="customer",
        resource_id=str(customer.id),
        metadata={"external_key": key},
    )
    await db.refresh(customer)
    return customer


async def list_customers(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    q: str | None = None,
):
    stmt = (
        select(Customer)
        .where(Customer.tenant_id == tenant_id)
        .order_by(Customer.updated_at.desc())
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
                Customer.external_key.ilike(like),
            )
        )
    return list((await db.execute(stmt.limit(200))).scalars().all())


async def get_customer(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> Customer:
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.id == customer_id,
            )
        )
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer not found")
    return customer


async def update_customer(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    **data,
):
    customer = await get_customer(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
    )
    for key, value in data.items():
        if value is not None:
            setattr(customer, key, value)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="customer.updated",
        resource_type="customer",
        resource_id=str(customer.id),
        metadata={"fields": sorted(data.keys())},
    )
    await db.refresh(customer)
    return customer
