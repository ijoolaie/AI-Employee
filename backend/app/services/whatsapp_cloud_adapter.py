"""WhatsApp Cloud API adapter boundary.

This adapter performs outbound delivery only when explicit provider
configuration is present. It never reports success without a provider response.
"""
from dataclasses import dataclass
import httpx
from app.services.channel_delivery import DeliveryResult, ChannelDeliveryError

class WhatsAppCloudAdapter:
    async def send_text(self, *, channel_config: dict, recipient: str, text: str) -> DeliveryResult:
        token = (channel_config or {}).get("access_token")
        phone_number_id = (channel_config or {}).get("phone_number_id")
        api_version = (channel_config or {}).get("api_version", "v23.0")
        if not token or not phone_number_id:
            raise ChannelDeliveryError("WhatsApp Cloud API credentials are not configured")
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        payload = {"messaging_product": "whatsapp", "to": recipient, "type": "text", "text": {"body": text}}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ChannelDeliveryError(f"WhatsApp provider rejected message: HTTP {response.status_code}")
        data = response.json()
        messages = data.get("messages") or []
        return DeliveryResult(provider_message_id=messages[0].get("id") if messages else None, status="accepted")
