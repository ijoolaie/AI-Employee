"""Provider-neutral outbound channel delivery boundary.

Concrete provider adapters consume opaque credential references and resolve
secrets only inside their infrastructure boundary. The application never
passes raw provider credentials through the channel configuration contract.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class ChannelDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeliveryResult:
    provider_message_id: str | None
    status: str
    detail: str | None = None


class ChannelAdapter(Protocol):
    async def send_text(
        self,
        *,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        channel_config: dict,
        recipient: str,
        text: str,
    ) -> DeliveryResult: ...


async def deliver_text(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_type: str,
    channel_config: dict,
    recipient: str,
    text: str,
) -> DeliveryResult:
    if channel_type == "whatsapp":
        provider = (channel_config or {}).get("provider")
        if provider == "whatsapp_cloud_api":
            from app.services.whatsapp_cloud_adapter import WhatsAppCloudAdapter

            return await WhatsAppCloudAdapter().send_text(
                db=db,
                tenant_id=tenant_id,
                channel_config=channel_config,
                recipient=recipient,
                text=text,
            )
    raise ChannelDeliveryError(f"No certified outbound adapter configured for channel type: {channel_type}")
