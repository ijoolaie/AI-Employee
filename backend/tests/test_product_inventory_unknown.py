"""Regression coverage for unknown versus verified product inventory."""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai import tool_registry
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.services import shopify_service


class _Result:
    def scalar_one_or_none(self):
        return None


class _FakeDB:
    def __init__(self):
        self.added = []
        self.flushes = 0

    async def execute(self, *_args, **_kwargs):
        return _Result()

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        self.flushes += 1


@pytest.mark.asyncio
@pytest.mark.parametrize(("provider_quantity", "expected"), [(None, None), (0, 0), (7, 7)])
async def test_shopify_sync_preserves_unknown_and_verified_inventory(monkeypatch, provider_quantity, expected):
    integration = SimpleNamespace(config={}, status="connected")
    db = _FakeDB()

    async def lock_integration(*_args):
        return integration

    async def paginate(*_args, **_kwargs):
        return [{
            "id": "gid://shopify/Product/1",
            "title": "Example",
            "status": "ACTIVE",
            "variants": {"nodes": [{
                "id": "gid://shopify/ProductVariant/1",
                "sku": "EXAMPLE",
                "price": "10.00",
                "inventoryQuantity": provider_quantity,
            }]},
            "images": {"nodes": []},
        }]

    monkeypatch.setattr(shopify_service, "_lock_integration", lock_integration)
    monkeypatch.setattr(shopify_service, "_paginate", paginate)
    await shopify_service.sync_products(db, uuid4(), uuid4())

    product = db.added[0]
    assert isinstance(product, Product)
    assert product.inventory is expected
    assert db.flushes == 2


def test_product_response_accepts_unknown_inventory():
    response = ProductResponse(
        id=uuid4(), name="Example", inventory=None, is_active=True, source="shopify",
        created_at="2026-10-31T00:00:00Z", updated_at="2026-10-31T00:00:00Z",
    )
    assert response.inventory is None


@pytest.mark.asyncio
async def test_check_inventory_does_not_claim_availability_when_unknown(monkeypatch):
    async def get_product(*_args, **_kwargs):
        return {"id": "p-1", "name": "Example", "inventory": None}

    monkeypatch.setattr(tool_registry, "_get_product", get_product)
    result = await tool_registry._check_inventory({"product_id": "p-1"})
    assert result["inventory"] is None
    assert result["available"] is None
    assert result["inventory_status"] == "unknown"


def test_manual_product_creation_keeps_zero_inventory_default():
    assert ProductCreate(name="Manual product").inventory == 0
