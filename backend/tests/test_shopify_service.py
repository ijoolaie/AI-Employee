from uuid import UUID, uuid4

import pytest

from app.services import shopify_service


def test_make_and_parse_shopify_state(monkeypatch):
    class Settings:
        secret_key = "x" * 48

    monkeypatch.setattr(shopify_service, "get_settings", lambda: Settings())
    tenant_id = uuid4()
    state = shopify_service.make_state(tenant_id)
    assert shopify_service.parse_state(state) == tenant_id


def test_parse_shopify_state_rejects_tampering(monkeypatch):
    class Settings:
        secret_key = "x" * 48

    monkeypatch.setattr(shopify_service, "get_settings", lambda: Settings())
    tenant_id = uuid4()
    state = shopify_service.make_state(tenant_id)
    tampered = state[:-2] + ("aa" if state[-2:] != "aa" else "bb")
    with pytest.raises(Exception):
        shopify_service.parse_state(tampered)


def test_verify_shopify_webhook(monkeypatch):
    import base64
    import hashlib
    import hmac

    class Settings:
        shopify_client_secret = "secret-for-test"

    monkeypatch.setattr(shopify_service, "get_settings", lambda: Settings())
    body = b'{"id":123,"name":"#1001"}'
    digest = base64.b64encode(hmac.new(Settings.shopify_client_secret.encode(), body, hashlib.sha256).digest()).decode()
    assert shopify_service.verify_webhook(body, digest) is True
    assert shopify_service.verify_webhook(body, "invalid") is False
    assert shopify_service.verify_webhook(body, None) is False
