import hashlib
import hmac
import json
import uuid

import pytest

from app.core.config import get_settings
from app.services import workforce_sales_inbound_provider


def _signed(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_sales_inbound_contract_provider_verifies_and_parses(monkeypatch):
    tenant_id = uuid.uuid4()
    secret = "w10-contract-secret"
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_inbound_provider_name", "contract-test")
    monkeypatch.setattr(
        settings,
        "sales_inbound_webhook_secrets",
        {str(tenant_id): secret},
    )

    body = json.dumps(
        {
            "provider_message_id": "outbox-message-1",
            "response_text": "Please send pricing.",
        },
        separators=(",", ":"),
    ).encode()

    result = workforce_sales_inbound_provider.parse_and_verify(
        tenant_id=tenant_id,
        body=body,
        event_id="evt-1",
        provider_message_id="outbox-message-1",
        signature=_signed(body, secret),
    )

    assert result.provider == "contract-test"
    assert result.event_key == "provider:contract-test:evt-1"
    assert result.provider_message_id == "outbox-message-1"
    assert result.response_text == "Please send pricing."


def test_sales_inbound_rejects_invalid_signature(monkeypatch):
    tenant_id = uuid.uuid4()
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_inbound_provider_name", "contract-test")
    monkeypatch.setattr(
        settings,
        "sales_inbound_webhook_secrets",
        {str(tenant_id): "correct-secret"},
    )

    with pytest.raises(Exception, match="Invalid sales inbound provider signature"):
        workforce_sales_inbound_provider.parse_and_verify(
            tenant_id=tenant_id,
            body=b'{"response_text":"hello"}',
            event_id="evt-1",
            provider_message_id="message-1",
            signature="wrong",
        )


def test_sales_inbound_fails_closed_when_provider_not_configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_inbound_provider_name", "none")

    with pytest.raises(Exception, match="not configured"):
        workforce_sales_inbound_provider.parse_and_verify(
            tenant_id=uuid.uuid4(),
            body=b'{"response_text":"hello"}',
            event_id="evt-1",
            provider_message_id="message-1",
            signature="unused",
        )
