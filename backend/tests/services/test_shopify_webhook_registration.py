from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import shopify_service


class _Settings:
    shopify_redirect_uri = "https://app.example.test/api/v1/commerce-integrations/shopify/callback"


class _LockResult:
    def __init__(self, integration):
        self.integration = integration

    def scalar_one_or_none(self):
        return self.integration


class _DB:
    def __init__(self, integration):
        self.integration = integration
        self.lock_queries = 0

    async def execute(self, statement):
        self.lock_queries += 1
        return _LockResult(self.integration)


@pytest.mark.asyncio
async def test_register_webhooks_does_not_create_existing_subscription(monkeypatch):
    integration = SimpleNamespace(id=uuid4(), config={})
    db = _DB(integration)
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

    result = await shopify_service.register_webhooks(db, integration)

    assert db.lock_queries == 1
    assert len(calls) == 8
    assert all("webhookSubscriptionCreate" not in call[0] for call in calls)
    assert all(item["status"] == "already_registered" for item in result)


@pytest.mark.asyncio
async def test_register_webhooks_creates_when_callback_is_missing(monkeypatch):
    integration = SimpleNamespace(id=uuid4(), config={})
    db = _DB(integration)
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

    result = await shopify_service.register_webhooks(db, integration)

    assert db.lock_queries == 1
    assert len(calls) == 16
    assert sum("webhookSubscriptionCreate" in call[0] for call in calls) == 8
    assert all(item["userErrors"] == [] for item in result)
