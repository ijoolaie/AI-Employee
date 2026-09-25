from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.models.product import Product
from app.services import product_service


class _Nested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _ProductDb:
    def __init__(self, *, fail_flush: bool = False):
        self.added = []
        self.fail_flush = fail_flush
        self.refreshed = []

    def begin_nested(self):
        return _Nested()

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        if self.fail_flush:
            orig = SimpleNamespace(constraint_name=product_service.PRODUCT_SKU_INDEX_NAME)
            raise IntegrityError("INSERT", {}, orig)

    async def refresh(self, row):
        self.refreshed.append(row)


class _LifecycleProductDb:
    def __init__(self, product):
        self.product = product
        self.refreshed = []
        self.flushes = 0

    async def execute(self, statement):
        return SimpleNamespace(scalar_one_or_none=lambda: self.product)

    def begin_nested(self):
        return _Nested()

    async def flush(self):
        self.flushes += 1

    async def refresh(self, row):
        self.refreshed.append(row)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        (" TEST-001 ", "TEST-001"),
        ("test-001", "TEST-001"),
        (" Test-001 ", "TEST-001"),
    ],
)
def test_normalize_sku(raw, expected):
    assert product_service.normalize_sku(raw) == expected


@pytest.mark.asyncio
async def test_create_product_normalizes_sku_before_persisting(monkeypatch):
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(product_service.audit_service, "record", record)
    db = _ProductDb()
    product = await product_service.create_product(
        db,
        uuid4(),
        {"sku": " test-001 ", "name": "Test", "price": 1},
        actor_id=uuid4(),
    )

    assert product.sku == "TEST-001"
    assert db.added == [product]
    assert db.refreshed == [product]
    assert audit[0]["action"] == "product.created"
    assert audit[0]["resource_id"] == str(product.id)


@pytest.mark.asyncio
async def test_create_product_maps_unique_sku_race_to_conflict():
    db = _ProductDb(fail_flush=True)

    with pytest.raises(ConflictError, match="Product SKU already exists in this tenant"):
        await product_service.create_product(
            db,
            uuid4(),
            {"sku": "TEST-001", "name": "Test", "price": 1},
        )

    assert len(db.added) == 1
    assert isinstance(db.added[0], Product)


@pytest.mark.asyncio
async def test_update_product_persists_change_and_audits_fields(monkeypatch):
    product = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        sku="OLD-SKU",
        name="Old name",
        price=10,
    )
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(product_service.audit_service, "record", record)
    db = _LifecycleProductDb(product)

    result = await product_service.update_product(
        db,
        product.tenant_id,
        product.id,
        {"name": "New name", "sku": " new-sku "},
        actor_id=uuid4(),
    )

    assert result is product
    assert product.name == "New name"
    assert product.sku == "NEW-SKU"
    assert db.flushes == 1
    assert db.refreshed == [product]
    assert audit == [{
        "tenant_id": product.tenant_id,
        "actor_id": actor_id,
        "action": "product.updated",
        "resource_type": "product",
        "resource_id": str(product.id),
        "metadata": {"fields": ["name", "sku"]},
    }]


@pytest.mark.asyncio
async def test_update_inventory_persists_change_and_audits_previous_value(monkeypatch):
    product = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        inventory=7,
    )
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(product_service.audit_service, "record", record)
    db = _LifecycleProductDb(product)

    result = await product_service.update_inventory(
        db,
        product.tenant_id,
        product.id,
        12,
        actor_id=uuid4(),
    )

    assert result is product
    assert product.inventory == 12
    assert db.flushes == 1
    assert db.refreshed == [product]
    assert audit[0]["action"] == "product.inventory_updated"
    assert audit[0]["tenant_id"] == product.tenant_id
    assert audit[0]["actor_id"] is not None
    assert audit[0]["resource_id"] == str(product.id)
    assert audit[0]["metadata"] == {"previous_inventory": 7, "inventory": 12}
