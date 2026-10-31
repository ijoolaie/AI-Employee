"""Regression tests for Shopify pagination completeness guarantees."""

from datetime import datetime\nfrom types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationAppError
from app.services import shopify_service


@pytest.mark.asyncio
async def test_paginate_accepts_completion_on_the_page_limit(monkeypatch):
    calls = []

    async def graphql(_db, _integration, _query, variables):
        calls.append(dict(variables))
        page = len(calls)
        return {
            "products": {
                "nodes": [{"id": str(page)}],
                "pageInfo": {
                    "hasNextPage": page < 2,
                    "endCursor": f"cursor-{page}" if page < 2 else None,
                },
            }
        }

    monkeypatch.setattr(shopify_service, "_graphql", graphql)

    rows = await shopify_service._paginate(
        None, None, "query", "products", page_size=1, max_pages=2
    )

    assert rows == [{"id": "1"}, {"id": "2"}]
    assert [call["after"] for call in calls] == [None, "cursor-1"]


@pytest.mark.asyncio
async def test_paginate_rejects_continuation_after_page_limit(monkeypatch):
    calls = []

    async def graphql(_db, _integration, _query, variables):
        calls.append(dict(variables))
        page = len(calls)
        return {
            "products": {
                "nodes": [{"id": str(page)}],
                "pageInfo": {"hasNextPage": True, "endCursor": f"cursor-{page}"},
            }
        }

    monkeypatch.setattr(shopify_service, "_graphql", graphql)

    with pytest.raises(ValidationAppError, match="exceeded the maximum page limit"):
        await shopify_service._paginate(
            None, None, "query", "products", page_size=1, max_pages=2
        )

    # The incomplete second page must not be returned as a successful result.
    assert len(calls) == 2
    assert [call["after"] for call in calls] == [None, "cursor-1"]


@pytest.mark.asyncio
@pytest.mark.parametrize("end_cursor", [None, "cursor-1"])
async def test_paginate_rejects_missing_or_repeated_cursor(monkeypatch, end_cursor):
    async def graphql(_db, _integration, _query, variables):
        return {
            "products": {
                "nodes": [{"id": "1"}],
                "pageInfo": {"hasNextPage": True, "endCursor": end_cursor},
            }
        }

    monkeypatch.setattr(shopify_service, "_graphql", graphql)

    with pytest.raises(ValidationAppError, match="without a new endCursor"):
        await shopify_service._paginate(
            None, None, "query", "products", page_size=1, max_pages=2
        )


@pytest.mark.asyncio
async def test_failed_product_pagination_does_not_advance_sync_metadata(monkeypatch):
    integration = SimpleNamespace(
        config={"last_product_sync_count": 7, "last_product_sync_at": "previous"}
    )

    async def lock_integration(*_args):
        return integration

    async def paginate(*_args, **_kwargs):
        raise ValidationAppError("Shopify pagination exceeded the maximum page limit")

    monkeypatch.setattr(shopify_service, "_lock_integration", lock_integration)
    monkeypatch.setattr(shopify_service, "_paginate", paginate)

    with pytest.raises(ValidationAppError):
        await shopify_service.sync_products(None, "tenant", "integration")

    assert integration.config == {
        "last_product_sync_count": 7,
        "last_product_sync_at": "previous",
    }


@pytest.mark.asyncio
async def test_failed_order_pagination_does_not_advance_sync_metadata(monkeypatch):
    from types import SimpleNamespace

    integration = SimpleNamespace(
        config={"last_order_sync_count": 9, "last_order_sync_at": "previous"}
    )

    async def lock_integration(*_args):
        return integration

    async def paginate(*_args, **_kwargs):
        raise ValidationAppError("Shopify pagination exceeded the maximum page limit")

    monkeypatch.setattr(shopify_service, "_lock_integration", lock_integration)
    monkeypatch.setattr(shopify_service, "_paginate", paginate)

    with pytest.raises(ValidationAppError):
        await shopify_service.sync_orders(None, "tenant", "integration")

    assert integration.config == {
        "last_order_sync_count": 9,
        "last_order_sync_at": "previous",
    }


@pytest.mark.asyncio
async def test_successful_product_sync_records_product_specific_freshness(monkeypatch):
    integration = SimpleNamespace(
        config={
            "shop_domain": "example.myshopify.com",
            "last_order_sync_at": "2026-10-30T12:00:00+00:00",
        },
        status="connected",
    )

    class FakeDB:
        flush_calls = 0

        async def flush(self):
            self.flush_calls += 1

    db = FakeDB()

    async def lock_integration(*_args):
        return integration

    async def paginate(*_args, **_kwargs):
        return []

    monkeypatch.setattr(shopify_service, "_lock_integration", lock_integration)
    monkeypatch.setattr(shopify_service, "_paginate", paginate)

    result = await shopify_service.sync_products(db, "tenant", "integration")

    assert result == {
        "provider": "shopify",
        "products_seen": 0,
        "created": 0,
        "updated": 0,
    }
    assert integration.status == "synced"
    assert integration.config["last_product_sync_count"] == 0
    assert integration.config["last_order_sync_at"] == "2026-10-30T12:00:00+00:00"
    freshness = datetime.fromisoformat(integration.config["last_product_sync_at"])
    assert freshness.tzinfo is not None
    assert db.flush_calls == 2
