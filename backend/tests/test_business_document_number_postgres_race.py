"""Real PostgreSQL concurrency coverage for business document numbers."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.exceptions import ConflictError
from app.core.database import AsyncSessionLocal
from app.models.business_invoice import BusinessInvoice
from app.models.business_order import BusinessOrder
from app.models.tenant import Tenant
from app.modules.employees.invoice import service as invoice_service
from app.modules.employees.order import service as order_service


@pytest_asyncio.fixture
async def business_document_number_setup(monkeypatch):
    async def record(*_args, **_kwargs):
        return None

    monkeypatch.setattr(invoice_service.audit_service, "record", record)
    monkeypatch.setattr(order_service.audit_service, "record", record)

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="Business Document Number Race Test",
            slug=f"doc-number-race-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.commit()
        tenant_id = tenant.id

    yield tenant_id

    async with AsyncSessionLocal() as db:
        await db.execute(delete(BusinessOrder).where(BusinessOrder.tenant_id == tenant_id))
        await db.execute(delete(BusinessInvoice).where(BusinessInvoice.tenant_id == tenant_id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_invoice_generation_produces_distinct_numbers(
    business_document_number_setup,
):
    tenant_id = business_document_number_setup

    async def create_one():
        async with AsyncSessionLocal() as db:
            invoice = await invoice_service.create_invoice(
                db,
                tenant_id=tenant_id,
                actor_id=None,
                customer_name="Concurrent Customer",
                line_items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
            )
            await db.commit()
            return invoice.number

    numbers = await asyncio.gather(*(create_one() for _ in range(16)))

    assert len(numbers) == 16
    assert len(set(numbers)) == 16
    assert all(number.startswith("INV-") for number in numbers)


@pytest.mark.asyncio
async def test_concurrent_order_generation_produces_distinct_numbers(
    business_document_number_setup,
):
    tenant_id = business_document_number_setup

    async def create_one():
        async with AsyncSessionLocal() as db:
            order = await order_service.create_order(
                db,
                tenant_id=tenant_id,
                actor_id=None,
                customer_name="Concurrent Customer",
                line_items=[{"description": "Widget", "quantity": 1, "unit_price": 100}],
            )
            await db.commit()
            return order.number

    numbers = await asyncio.gather(*(create_one() for _ in range(16)))

    assert len(numbers) == 16
    assert len(set(numbers)) == 16
    assert all(number.startswith("ORD-") for number in numbers)


@pytest.mark.asyncio
async def test_concurrent_duplicate_invoice_number_is_db_enforced(
    business_document_number_setup,
):
    tenant_id = business_document_number_setup
    number = "INV-MANUAL-RACE-001"

    async def create_one():
        async with AsyncSessionLocal() as db:
            try:
                invoice = await invoice_service.create_invoice(
                    db,
                    tenant_id=tenant_id,
                    actor_id=None,
                    customer_name="Concurrent Customer",
                    line_items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
                    number=number,
                )
                await db.commit()
                return "created", invoice.id
            except ConflictError:
                await db.rollback()
                return "conflict", None

    results = await asyncio.gather(create_one(), create_one())

    assert sorted(result[0] for result in results) == ["conflict", "created"]

    async with AsyncSessionLocal() as db:
        rows = list(
            (
                await db.execute(
                    select(BusinessInvoice).where(
                        BusinessInvoice.tenant_id == tenant_id,
                        BusinessInvoice.number == number,
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_concurrent_duplicate_order_number_is_db_enforced(
    business_document_number_setup,
):
    tenant_id = business_document_number_setup
    number = "ORD-MANUAL-RACE-001"

    async def create_one():
        async with AsyncSessionLocal() as db:
            try:
                order = await order_service.create_order(
                    db,
                    tenant_id=tenant_id,
                    actor_id=None,
                    customer_name="Concurrent Customer",
                    line_items=[{"description": "Widget", "quantity": 1, "unit_price": 100}],
                    number=number,
                )
                await db.commit()
                return "created", order.id
            except ConflictError:
                await db.rollback()
                return "conflict", None

    results = await asyncio.gather(create_one(), create_one())

    assert sorted(result[0] for result in results) == ["conflict", "created"]

    async with AsyncSessionLocal() as db:
        rows = list(
            (
                await db.execute(
                    select(BusinessOrder).where(
                        BusinessOrder.tenant_id == tenant_id,
                        BusinessOrder.number == number,
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(rows) == 1
