"""Provider-neutral outbound channel delivery boundary.

Concrete provider adapters (for example WhatsApp Cloud API) belong behind this
interface. The application never treats a database-only message as delivered.
"""
from dataclasses import dataclass
from typing import Protocol

class ChannelDeliveryError(RuntimeError):
    pass

@dataclass(frozen=True)
class DeliveryResult:
    provider_message_id: str | None
    status: str
    detail: str | None = None

class ChannelAdapter(Protocol):
    async def send_text(self, *, channel_config: dict, recipient: str, text: str) -> DeliveryResult: ...

async def deliver_text(*, channel_type: str, channel_config: dict, recipient: str, text: str) -> DeliveryResult:
    if channel_type == "whatsapp":
        provider = (channel_config or {}).get("provider")
        if provider == "whatsapp_cloud_api":
            # Provider credential/API implementation is intentionally isolated;
            # certification happens in the final verification phase.
            from app.services.whatsapp_cloud_adapter import WhatsAppCloudAdapter
            return await WhatsAppCloudAdapter().send_text(channel_config=channel_config, recipient=recipient, text=text)
    raise ChannelDeliveryError(f"No certified outbound adapter configured for channel type: {channel_type}")
