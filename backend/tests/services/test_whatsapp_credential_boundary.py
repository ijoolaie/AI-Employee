from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.channel_delivery import ChannelDeliveryError
from app.services.whatsapp_cloud_adapter import WhatsAppCloudAdapter


@pytest.mark.asyncio
async def test_whatsapp_rejects_legacy_plaintext_access_token():
    with pytest.raises(ChannelDeliveryError, match="opaque credential reference"):
        await WhatsAppCloudAdapter().send_text(
            db=object(),
            tenant_id=uuid4(),
            channel_config={
                "provider": "whatsapp_cloud_api",
                "phone_number_id": "123",
                "access_token": "plaintext-secret",
            },
            recipient="15551234567",
            text="hello",
        )


@pytest.mark.asyncio
async def test_whatsapp_rejects_malformed_credential_reference():
    with pytest.raises(ChannelDeliveryError, match="credential reference is invalid"):
        await WhatsAppCloudAdapter().send_text(
            db=object(),
            tenant_id=uuid4(),
            channel_config={
                "provider": "whatsapp_cloud_api",
                "phone_number_id": "123",
                "credential_refs": {"access_token": "not-a-credential-ref"},
            },
            recipient="15551234567",
            text="hello",
        )
