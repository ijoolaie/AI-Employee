import pytest
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1 import commerce_integrations


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Db:
    def __init__(self):
        self.events = []
        self.added = []

    async def execute(self, _statement):
        return _ScalarResult(None)

    def add(self, value):
        self.events.append("add")
        self.added.append(value)

    async def flush(self):
        self.events.append("flush")

    async def commit(self):
        self.events.append("commit")


@pytest.mark.asyncio
async def test_shopify_oauth_commits_token_before_webhook_side_effect(monkeypatch):
    tenant_id = uuid4()
    db = _Db()
    credential = SimpleNamespace(id=uuid4())
    webhook_events = []

    monkeypatch.setattr(
        commerce_integrations.shopify_oauth_state,
        "consume_state",
        lambda *_args: _async_value(tenant_id),
    )
    monkeypatch.setattr(
        commerce_integrations.shopify_service,
        "exchange_code",
        lambda *_args: _async_value({"access_token": "token", "scope": "read_products"}),
    )
    monkeypatch.setattr(
        commerce_integrations,
        "store_credential",
        lambda *_args, **_kwargs: _async_value(credential),
    )
    monkeypatch.setattr(
        commerce_integrations,
        "credential_ref",
        lambda value: f"cred:{value.id}",
    )

    async def register(_db, _row):
        webhook_events.append(("webhooks", list(_db.events)))

    monkeypatch.setattr(commerce_integrations.shopify_service, "register_webhooks", register)
    monkeypatch.setattr(
        commerce_integrations,
        "get_settings",
        lambda: SimpleNamespace(
            shopify_api_version="2026-07",
            frontend_app_url="https://app.example.test",
        ),
    )
    monkeypatch.setattr(
        commerce_integrations.audit_service,
        "record",
        lambda *_args, **_kwargs: _async_value(None),
    )

    response = await commerce_integrations.shopify_callback(
        shop="store.myshopify.com",
        code="oauth-code",
        state="state",
        db=db,
    )

    assert response.status_code == 302
    assert db.events.index("commit") < webhook_events[0][1].index("webhooks") if "webhooks" in webhook_events[0][1] else True
    assert webhook_events == [("webhooks", ["add", "flush", "commit"])]


async def _async_value(value):
    return value
