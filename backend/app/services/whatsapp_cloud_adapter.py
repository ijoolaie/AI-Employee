"""WhatsApp Cloud API adapter boundary.

Outbound delivery consumes only opaque credential references. Raw provider
secrets are resolved inside this infrastructure boundary and are never read
from channel configuration.
"""
from __future__ import annotations

import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.channel_delivery import DeliveryResult, ChannelDeliveryError
from app.services.credential_service import resolve_credential


class WhatsAppCloudAdapter:
    async def send_text(
        self,
        *,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        channel_config: dict,
        recipient: str,
        text: str,
    ) -> DeliveryResult:
        config = channel_config or {}
        refs = config.get("credential_refs") or {}
        credential_ref = refs.get("access_token")
        phone_number_id = config.get("phone_number_id")
        api_version = config.get("api_version", "v23.0")
        if not credential_ref or not phone_number_id:
            if config.get("access_token"):
                raise ChannelDeliveryError("WhatsApp Cloud API requires an opaque credential reference")
            raise ChannelDeliveryError("WhatsApp Cloud API credentials are not configured")
        if not isinstance(credential_ref, str) or not credential_ref.startswith("cred:"):
            raise ChannelDeliveryError("WhatsApp Cloud API credential reference is invalid")
        try:
            credential_id = uuid.UUID(credential_ref.removeprefix("cred:"))
        except ValueError as exc:
            raise ChannelDeliveryError("WhatsApp Cloud API credential reference is invalid") from exc

        try:
            token = await resolve_credential(
                db,
                tenant_id=tenant_id,
                credential_id=credential_id,
                tool_name="whatsapp.send_text",
            )
        except Exception as exc:
            if isinstance(exc, ChannelDeliveryError):
                raise
            raise ChannelDeliveryError("WhatsApp Cloud API credential could not be resolved") from exc

        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ChannelDeliveryError(f"WhatsApp provider rejected message: HTTP {response.status_code}")
        data = response.json()
        messages = data.get("messages") or []
        return DeliveryResult(provider_message_id=messages[0].get("id") if messages else None, status="accepted")
