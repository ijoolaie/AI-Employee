from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.modules.employees.invoice import service as invoice_service
from app.modules.employees.order import service as order_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _LifecycleDb:
    def __init__(self, value=None):
        self.value = value
        self.added = []
        self.flushes = 0

    def add(self, row):
        self.added.append(row)

    async def execute(self, _statement):
        return _Result(self.value)

    async def flush(self):
        self.flushes += 1


@pytest.mark.asyncio
async def test_create_order_persists_and_audits_actor(monkeypatch):
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(order_service.audit_service, "record", record)
    db = _LifecycleDb()
    tenant_id = uuid4()
    actor_id = uuid4()

    order = await order_service.create_order(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        customer_name="Customer",
        line_items=[{"description": "Widget", "quantity": 2, "unit_price": 100}],
    )

    assert db.added == [order]
    assert db.flushes == 1
    assert order.tenant_id == tenant_id
    assert order.created_by == actor_id
    assert audit == [{
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "action": "order.created",
        "resource_type": "business_order",
        "resource_id": str(order.id),
        "metadata": {
            "number": order.number,
            "total": 200.0,
            "currency": "IRR",
        },
    }]


@pytest.mark.asyncio
async def test_update_order_audits_changed_fields_and_actor(monkeypatch):
    order = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        status="draft",
        customer_name="Old",
        currency="IRR",
        line_items=[{"description": "Widget", "quantity": 1, "unit_price": 100, "amount": 100}],
        tax_rate=0,
    )
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(order_service.audit_service, "record", record)
    db = _LifecycleDb(order)
    actor_id = uuid4()

    result = await order_service.update_order(
        db,
        tenant_id=order.tenant_id,
        actor_id=actor_id,
        order_id=str(order.id),
        customer_name="New",
    )

    assert result is order
    assert order.customer_name == "New"
    assert db.flushes == 1
    assert audit[0]["action"] == "order.updated"
    assert audit[0]["actor_id"] == actor_id
    assert audit[0]["resource_id"] == str(order.id)
    assert audit[0]["metadata"] == {"fields": ["customer_name"]}


@pytest.mark.asyncio
async def test_update_order_status_is_tenant_scoped_and_audited(monkeypatch):
    order = SimpleNamespace(id=uuid4(), tenant_id=uuid4(), status="draft")
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(order_service.audit_service, "record", record)
    db = _LifecycleDb(order)
    actor_id = uuid4()

    result = await order_service.update_status(
        db,
        tenant_id=order.tenant_id,
        actor_id=actor_id,
        order_id=str(order.id),
        status="confirmed",
    )

    assert result is order
    assert order.status == "confirmed"
    assert audit[0]["action"] == "order.status_updated"
    assert audit[0]["tenant_id"] == order.tenant_id
    assert audit[0]["actor_id"] == actor_id
    assert audit[0]["metadata"] == {"status": "confirmed"}


@pytest.mark.asyncio
async def test_create_invoice_persists_and_audits_actor(monkeypatch):
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(invoice_service.audit_service, "record", record)
    db = _LifecycleDb()
    tenant_id = uuid4()
    actor_id = uuid4()

    invoice = await invoice_service.create_invoice(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        customer_name="Customer",
        line_items=[{"description": "Service", "quantity": 2, "unit_price": 100}],
    )

    assert db.added == [invoice]
    assert db.flushes == 1
    assert invoice.tenant_id == tenant_id
    assert invoice.created_by == actor_id
    assert audit == [{
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "action": "invoice.created",
        "resource_type": "business_invoice",
        "resource_id": str(invoice.id),
        "metadata": {
            "number": invoice.number,
            "total": 200.0,
            "currency": "IRR",
        },
    }]


@pytest.mark.asyncio
async def test_update_invoice_audits_changed_fields_and_actor(monkeypatch):
    invoice = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        status="draft",
        customer_name="Old",
        currency="IRR",
        line_items=[{"description": "Service", "quantity": 1, "unit_price": 100, "amount": 100}],
        tax_rate=0,
    )
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(invoice_service.audit_service, "record", record)
    db = _LifecycleDb(invoice)
    actor_id = uuid4()

    result = await invoice_service.update_invoice(
        db,
        tenant_id=invoice.tenant_id,
        actor_id=actor_id,
        invoice_id=str(invoice.id),
        customer_name="New",
    )

    assert result is invoice
    assert invoice.customer_name == "New"
    assert db.flushes == 1
    assert audit[0]["action"] == "invoice.updated"
    assert audit[0]["actor_id"] == actor_id
    assert audit[0]["resource_id"] == str(invoice.id)
    assert audit[0]["metadata"] == {"fields": ["customer_name"]}


@pytest.mark.asyncio
async def test_update_invoice_status_rejects_invalid_status_before_lookup():
    with pytest.raises(ValidationAppError, match="status must be one of"):
        await invoice_service.update_status(
            _LifecycleDb(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            invoice_id=str(uuid4()),
            status="unknown",
        )


@pytest.mark.asyncio
async def test_update_invoice_status_is_tenant_scoped_and_audited(monkeypatch):
    invoice = SimpleNamespace(id=uuid4(), tenant_id=uuid4(), status="draft")
    audit = []

    async def record(*_args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(invoice_service.audit_service, "record", record)
    db = _LifecycleDb(invoice)
    actor_id = uuid4()

    result = await invoice_service.update_status(
        db,
        tenant_id=invoice.tenant_id,
        actor_id=actor_id,
        invoice_id=str(invoice.id),
        status="paid",
    )

    assert result is invoice
    assert invoice.status == "paid"
    assert audit[0]["action"] == "invoice.status_updated"
    assert audit[0]["tenant_id"] == invoice.tenant_id
    assert audit[0]["actor_id"] == actor_id
    assert audit[0]["resource_id"] == str(invoice.id)
    assert audit[0]["metadata"] == {"status": "paid"}


@pytest.mark.asyncio
async def test_update_invoice_is_tenant_scoped_before_mutation(monkeypatch):
    with pytest.raises(NotFoundError, match="Invoice not found"):
        await invoice_service.update_invoice(
            _LifecycleDb(None),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            invoice_id=str(uuid4()),
            customer_name="Other tenant",
        )
