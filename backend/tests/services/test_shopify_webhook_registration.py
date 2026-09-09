from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import shopify_service


class _Settings:
    shopify_redirect_uri = "https://app.example.test/api/v1/commerce-integrations/shopify/callback"


@pytest.mark.asyncio
async def test_register_webhooks_does_not_create_existing_subscription(monkeypatch):
    integration = SimpleNamespace(id=uuid4(), config={})
    calls = []

    async def graphql(db, integration_arg, query, variables=None):
        calls.append((query, variables))
        return {
            "webhookSubscriptions": {
                "nodes": [
                    {
                        "id": "gid://shopify/WebhookSubscription/1",
                        "topic": variables["topic"],
                        "uri": "https://app.example.test/api/v1/commerce-integrations/shopify/webhooks/" + str(integration.id),
                    }
                ]
            }
        }

    monkeypatch.setattr(shopify_service, "get_settings", lambda: _Settings())
    monkeypatch.setattr(shopify_service, "_graphql", graphql)

    result = await shopify_service.register_webhooks(None, integration)

    assert len(calls) == 8
    assert all("webhookSubscriptionCreate" not in call[0] for call in calls)
    assert all(item["status"] == "already_registered" for item in result)


@pytest.mark.asyncio
async def test_register_webhooks_creates_when_callback_is_missing(monkeypatch):
    integration = SimpleNamespace(id=uuid4(), config={})
    calls = []

    async def graphql(db, integration_arg, query, variables=None):
        calls.append((query, variables))
        if "webhookSubscriptions" in query:
            return {"webhookSubscriptions": {"nodes": []}}
        return {
            "webhookSubscriptionCreate": {
                "webhookSubscription": {
                    "id": "gid://shopify/WebhookSubscription/new",
                    "topic": variables["topic"],
                    "uri": variables["callbackUrl"],
                },
                "userErrors": [],
            }
        }

    monkeypatch.setattr(shopify_service, "get_settings", lambda: _Settings())
    monkeypatch.setattr(shopify_service, "_graphql", graphql)

    result = await shopify_service.register_webhooks(None, integration)

    assert len(calls) == 16
    assert sum("webhookSubscriptionCreate" in call[0] for call in calls) == 8
    assert all(item["userErrors"] == [] for item in result)
