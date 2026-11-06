import hashlib
import hmac
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1 import channel_webhooks


def _request(body: bytes) -> Request:
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {"type": "http", "method": "POST", "path": "/webhooks/channels/whatsapp/test", "headers": []},
        receive,
    )


class _Db:
    def __init__(self, channel):
        self.channel = channel

    async def execute(self, _statement):
        return SimpleNamespace(scalar_one_or_none=lambda: self.channel)


@pytest.mark.asyncio
async def test_whatsapp_channel_webhook_signs_entire_raw_payload(monkeypatch):
    channel_id = uuid4()
    channel = SimpleNamespace(
        id=channel_id,
        tenant_id=uuid4(),
        employee_id=uuid4(),
        channel_type="whatsapp",
        is_active=True,
        config={"webhook_secret": "test-secret"},
    )
    body = json.dumps(
        {
            "from_phone": "+49123456789",
            "text": "hello",
            "name": "Alice",
            "message_id": "provider-message-1",
        },
        separators=(",", ":"),
    ).encode()
    payload = channel_webhooks.WhatsAppInbound.model_validate_json(body)
    signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    captured = {}

    async def enqueue(_db, received_channel, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id=uuid4()), uuid4(), False

    monkeypatch.setattr(channel_webhooks, "_enqueue_whatsapp_message", enqueue)
    result = await channel_webhooks.whatsapp_inbound(
        channel_id, payload, _request(body), _Db(channel), signature
    )

    assert result["success"] is True
    assert captured == {
        "from_phone": "+49123456789",
        "text": "hello",
        "name": "Alice",
        "provider_message_id": "provider-message-1",
    }


@pytest.mark.asyncio
async def test_whatsapp_channel_webhook_rejects_text_only_signature(monkeypatch):
    channel = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        employee_id=uuid4(),
        channel_type="whatsapp",
        is_active=True,
        config={"webhook_secret": "test-secret"},
    )
    body = b'{"from_phone":"+49999999999","text":"hello","name":"Mallory","message_id":"forged"}'
    payload = channel_webhooks.WhatsAppInbound.model_validate_json(body)
    text_only_signature = hmac.new(
        b"test-secret", payload.text.encode(), hashlib.sha256
    ).hexdigest()

    with pytest.raises(HTTPException) as exc:
        await channel_webhooks.whatsapp_inbound(
            channel.id, payload, _request(body), _Db(channel), text_only_signature
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_whatsapp_channel_webhook_fails_closed_without_secret(monkeypatch):
    channel = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        employee_id=uuid4(),
        channel_type="whatsapp",
        is_active=True,
        config={},
    )
    body = b'{"from_phone":"+49123456789","text":"hello"}'
    payload = channel_webhooks.WhatsAppInbound.model_validate_json(body)

    with pytest.raises(HTTPException) as exc:
        await channel_webhooks.whatsapp_inbound(
            channel.id, payload, _request(body), _Db(channel), None
        )

    assert exc.value.status_code == 503
