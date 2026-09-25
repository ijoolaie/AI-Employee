from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import commerce_integration_service, customer_channel_service


class _AuditDb:
    def __init__(self):
        self.added = []
        self.flushes = 0
        self.refreshed = []

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flushes += 1

    async def refresh(self, row):
        self.refreshed.append(row)


@pytest.mark.asyncio
async def test_create_channel_persists_and_audits_actor(monkeypatch):
    tenant_id = uuid4()
    employee_id = uuid4()
    actor_id = uuid4()
    employee = SimpleNamespace(id=employee_id)
    audit = []
    tenant_id_expected = tenant_id

    async def get_employee(db, *, employee_id, tenant_id):
        assert employee_id == employee.id
        assert tenant_id == tenant_id_expected
        return employee

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(customer_channel_service.employee_service, "get_employee", get_employee)
    monkeypatch.setattr(customer_channel_service.audit_service, "record", record)

    db = _AuditDb()
    channel = await customer_channel_service.create_channel(
        db,
        tenant_id=tenant_id,
        employee_id=employee_id,
        name="Public Chat",
        channel_type="web_widget",
        config={"locale": "fa"},
        actor_id=actor_id,
    )

    assert db.added == [channel]
    assert db.flushes == 1
    assert db.refreshed == [channel]
    assert channel.tenant_id == tenant_id
    assert channel.employee_id == employee_id
    assert audit == [{
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "action": "customer.channel.created",
        "resource_type": "customer_channel",
        "resource_id": channel.id,
        "metadata": {
            "employee_id": str(employee_id),
            "channel_type": "web_widget",
        },
    }]


@pytest.mark.asyncio
async def test_create_integration_persists_and_audits_actor(monkeypatch):
    tenant_id = uuid4()
    actor_id = uuid4()
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(commerce_integration_service.audit_service, "record", record)

    db = _AuditDb()
    integration = await commerce_integration_service.create_integration(
        db,
        tenant_id=tenant_id,
        provider="shopify",
        name="Store",
        config={"shop_domain": "example.myshopify.com"},
        actor_id=actor_id,
    )

    assert db.added == [integration]
    assert db.flushes == 1
    assert db.refreshed == [integration]
    assert integration.tenant_id == tenant_id
    assert integration.provider == "shopify"
    assert integration.config == {"shop_domain": "example.myshopify.com"}
    assert audit == [{
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "action": "commerce.integration.created",
        "resource_type": "commerce_integration",
        "resource_id": integration.id,
        "metadata": {"provider": "shopify", "name": "Store"},
    }]
