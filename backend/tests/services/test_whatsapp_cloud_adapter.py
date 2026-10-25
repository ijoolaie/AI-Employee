"""Contract tests for the Meta WhatsApp Cloud outbound adapter.

These tests mock the HTTP boundary; they do not send real WhatsApp messages.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.channel_delivery import ChannelDeliveryError, DeliveryResult
from app.services.whatsapp_cloud_adapter import WhatsAppCloudAdapter


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *, timeout: float):
        self.timeout = timeout
        self.calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, *, json: dict, headers: dict):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


@pytest.mark.asyncio
async def test_cloud_adapter_resolves_opaque_credential_and_returns_provider_message_id(monkeypatch):
    tenant_id = uuid4()
    credential_id = uuid4()
    resolved = []

    async def resolve(db, *, tenant_id, credential_id, tool_name):
        resolved.append((db, tenant_id, credential_id, tool_name))
        return "test-access-token"

    client = FakeAsyncClient(timeout=15)
    client.response = FakeResponse(
        200,
        {"messaging_product": "whatsapp", "messages": [{"id": "wamid.test-123"}]},
    )
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.resolve_credential", resolve)
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.httpx.AsyncClient", lambda *, timeout: client)

    db = object()
    result = await WhatsAppCloudAdapter().send_text(
        db=db,
        tenant_id=tenant_id,
        channel_config={
            "provider": "whatsapp_cloud_api",
            "phone_number_id": "123456789",
            "api_version": "v23.0",
            "credential_refs": {"access_token": f"cred:{credential_id}"},
        },
        recipient="15551234567",
        text="Hello from a test",
    )

    assert result == DeliveryResult(provider_message_id="wamid.test-123", status="accepted")
    assert resolved == [(db, tenant_id, credential_id, "whatsapp.send_text")]
    assert client.timeout == 15
    assert client.calls == [
        {
            "url": "https://graph.facebook.com/v23.0/123456789/messages",
            "json": {
                "messaging_product": "whatsapp",
                "to": "15551234567",
                "type": "text",
                "text": {"body": "Hello from a test"},
            },
            "headers": {
                "Authorization": "Bearer test-access-token",
                "Content-Type": "application/json",
            },
        }
    ]


@pytest.mark.asyncio
async def test_cloud_adapter_rejects_provider_http_error_without_echoing_response_body(monkeypatch):
    async def resolve(db, *, tenant_id, credential_id, tool_name):
        return "test-access-token"

    client = FakeAsyncClient(timeout=15)
    client.response = FakeResponse(401, {"error": {"message": "token should not appear in logs"}})
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.resolve_credential", resolve)
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.httpx.AsyncClient", lambda *, timeout: client)

    with pytest.raises(ChannelDeliveryError, match="HTTP 401") as exc_info:
        await WhatsAppCloudAdapter().send_text(
            db=object(),
            tenant_id=uuid4(),
            channel_config={
                "provider": "whatsapp_cloud_api",
                "phone_number_id": "123456789",
                "credential_refs": {"access_token": f"cred:{uuid4()}"},
            },
            recipient="15551234567",
            text="Hello",
        )

    assert "test-access-token" not in str(exc_info.value)
    assert "token should not appear in logs" not in str(exc_info.value)
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_cloud_adapter_does_not_call_provider_if_credential_resolution_fails(monkeypatch):
    async def resolve(db, *, tenant_id, credential_id, tool_name):
        raise RuntimeError("internal vault detail")

    client = FakeAsyncClient(timeout=15)
    client.response = FakeResponse(200, {"messages": [{"id": "should-not-exist"}]})
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.resolve_credential", resolve)
    monkeypatch.setattr("app.services.whatsapp_cloud_adapter.httpx.AsyncClient", lambda *, timeout: client)

    with pytest.raises(ChannelDeliveryError, match="credential could not be resolved") as exc_info:
        await WhatsAppCloudAdapter().send_text(
            db=object(),
            tenant_id=uuid4(),
            channel_config={
                "provider": "whatsapp_cloud_api",
                "phone_number_id": "123456789",
                "credential_refs": {"access_token": f"cred:{uuid4()}"},
            },
            recipient="15551234567",
            text="Hello",
        )

    assert "internal vault detail" not in str(exc_info.value)
    assert client.calls == []
