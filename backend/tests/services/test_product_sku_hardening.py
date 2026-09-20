from __future__ import annotations

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
            raise IntegrityError("INSERT", {}, Exception("duplicate key"))

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
async def test_create_product_normalizes_sku_before_persisting():
    db = _ProductDb()
    product = await product_service.create_product(
        db,
        uuid4(),
        {"sku": " test-001 ", "name": "Test", "price": 1},
    )

    assert product.sku == "TEST-001"
    assert db.added == [product]
    assert db.refreshed == [product]


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
