from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.requests import Request
from fastapi import HTTPException

from app.api.v1 import commerce_integrations


def _request(body: bytes = b"{}") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/commerce-integrations/shopify/webhooks/test",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 443),
            "scheme": "https",
        }
    )


@pytest.mark.asyncio
async def test_shopify_webhook_rejects_missing_delivery_id(monkeypatch):
    monkeypatch.setattr(
        commerce_integrations.shopify_service,
        "verify_webhook",
        lambda body, signature: True,
    )

    with pytest.raises(HTTPException) as exc:
        await commerce_integrations.shopify_webhook(
            uuid4(),
            _request(),
            SimpleNamespace(),
            x_shopify_hmac_sha256="valid",
            x_shopify_webhook_id=None,
            x_shopify_topic="ORDERS_CREATE",
            x_shopify_shop_domain="shop.example",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Missing Shopify webhook delivery ID"


@pytest.mark.asyncio
async def test_shopify_webhook_rejects_blank_delivery_id(monkeypatch):
    monkeypatch.setattr(
        commerce_integrations.shopify_service,
        "verify_webhook",
        lambda body, signature: True,
    )

    with pytest.raises(HTTPException) as exc:
        await commerce_integrations.shopify_webhook(
            uuid4(),
            _request(),
            SimpleNamespace(),
            x_shopify_hmac_sha256="valid",
            x_shopify_webhook_id="   ",
            x_shopify_topic="ORDERS_CREATE",
            x_shopify_shop_domain="shop.example",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Missing Shopify webhook delivery ID"
