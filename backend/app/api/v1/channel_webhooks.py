import hashlib
import hmac
import json
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession
from app.models.customer_channel import CustomerChannel
from app.services import customer_channel_service
from app.services import whatsapp_meta_service

router = APIRouter(prefix="/webhooks/channels", tags=["channel-webhooks"])


class WhatsAppInbound(BaseModel):
    from_phone: str = Field(min_length=3, max_length=40)
    text: str = Field(min_length=1, max_length=8000)
    name: str | None = None
    message_id: str | None = None


async def _enqueue_whatsapp_message(
    db,
    channel: CustomerChannel,
    *,
    from_phone: str,
    text: str,
    name: str | None = None,
    provider_message_id: str | None = None,
):
    from app.models.conversation import CustomerConversation, CustomerMessage
    from app.services import run_service

    external_key = "wa:" + from_phone

    if provider_message_id:
        duplicate = (
            await db.execute(
                select(CustomerMessage)
                .where(
                    CustomerMessage.tenant_id == channel.tenant_id,
                    CustomerMessage.channel_id == channel.id,
                    CustomerMessage.provider_message_id == provider_message_id,
                )
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            existing = (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.id == duplicate.conversation_id
                    )
                )
            ).scalar_one()
            return existing, duplicate.run_id, True

    existing = (
        await db.execute(
            select(CustomerConversation)
            .where(
                CustomerConversation.channel_id == channel.id,
                CustomerConversation.external_conversation_key == external_key,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        # Compatibility path for conversations created before v1.4.8. Lock the
        # legacy phone-based row before assigning its stable external key.
        existing = (
            await db.execute(
                select(CustomerConversation)
                .where(
                    CustomerConversation.channel_id == channel.id,
                    CustomerConversation.customer_phone == from_phone,
                    CustomerConversation.external_conversation_key.is_(None),
                )
                .order_by(CustomerConversation.updated_at.desc())
                .with_for_update()
            )
        ).scalars().first()

    if existing is None:
        customer = await customer_channel_service.customer_service.upsert_customer(
            db,
            tenant_id=channel.tenant_id,
            external_key=from_phone,
            name=name,
            phone=from_phone,
            channel="whatsapp",
        )
        candidate = CustomerConversation(
            tenant_id=channel.tenant_id,
            employee_id=channel.employee_id,
            channel_id=channel.id,
            customer_token_hash=hashlib.sha256(external_key.encode()).hexdigest(),
            customer_name=name,
            customer_phone=from_phone,
            customer_id=customer.id,
            external_conversation_key=external_key,
        )
        db.add(candidate)
        try:
            async with db.begin_nested():
                await db.flush()
            existing = candidate
        except IntegrityError:
            existing = (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.channel_id == channel.id,
                        CustomerConversation.external_conversation_key == external_key,
                    )
                )
            ).scalar_one()
    elif existing.external_conversation_key is None:
        existing.external_conversation_key = external_key
        if name and not existing.customer_name:
            existing.customer_name = name
        await db.flush()

    message = CustomerMessage(
        tenant_id=channel.tenant_id,
        conversation_id=existing.id,
        channel_id=channel.id,
        provider_message_id=provider_message_id,
        role="user",
        content=text,
    )
    db.add(message)
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        if provider_message_id:
            duplicate = (
                await db.execute(
                    select(CustomerMessage).where(
                        CustomerMessage.tenant_id == channel.tenant_id,
                        CustomerMessage.channel_id == channel.id,
                        CustomerMessage.provider_message_id == provider_message_id,
                    )
                )
            ).scalar_one()
            return existing, duplicate.run_id, True
        raise

    run = await run_service.create_run(
        db,
        tenant_id=channel.tenant_id,
        employee_id=channel.employee_id,
        input_data={
            "message": text,
            "customer": {
                "name": existing.customer_name,
                "phone": from_phone,
            },
            "channel": "whatsapp",
        },
        created_by=None,
        employee_version_id=None,
    )
    run.conversation_id = existing.id
    message.run_id = run.id

    try:
        from app.workers.run_worker import execute_run_task

        execute_run_task.delay(str(run.id))
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Run queue unavailable; retry webhook",
        ) from exc

    return existing, run.id, False


@router.post("/whatsapp/{channel_id}")
async def whatsapp_inbound(
    channel_id: UUID,
    payload: WhatsAppInbound,
    db: DbSession,
    x_channel_signature: str | None = Header(default=None),
):
    channel = (
        await db.execute(
            select(CustomerChannel).where(
                CustomerChannel.id == channel_id,
                CustomerChannel.channel_type == "whatsapp",
                CustomerChannel.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    secret = (channel.config or {}).get("webhook_secret")
    if secret:
        expected = hmac.new(
            secret.encode(), payload.text.encode(), hashlib.sha256
        ).hexdigest()
        if not x_channel_signature or not hmac.compare_digest(
            expected, x_channel_signature
        ):
            raise HTTPException(status_code=401, detail="Invalid channel signature")

    existing, run_id, duplicate = await _enqueue_whatsapp_message(
        db,
        channel,
        from_phone=payload.from_phone,
        text=payload.text,
        name=payload.name,
        provider_message_id=payload.message_id,
    )
    return {
        "success": True,
        "conversation_id": str(existing.id),
        "run_id": str(run_id) if run_id else None,
        "duplicate": duplicate,
        "delivery": "provider_adapter_required",
    }


@router.get("/whatsapp/meta/{channel_id}")
async def whatsapp_meta_verify(
    channel_id: UUID,
    db: DbSession,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    channel = (
        await db.execute(
            select(CustomerChannel).where(
                CustomerChannel.id == channel_id,
                CustomerChannel.channel_type == "whatsapp",
                CustomerChannel.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")
    challenge = whatsapp_meta_service.verify_webhook_challenge(
        hub_mode,
        hub_verify_token,
        hub_challenge,
        (channel.config or {}).get("meta_verify_token"),
    )
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid WhatsApp verification challenge",
        )
    return challenge


@router.post("/whatsapp/meta/{channel_id}", status_code=status.HTTP_200_OK)
async def whatsapp_meta_inbound(
    channel_id: UUID,
    request: Request,
    db: DbSession,
    x_hub_signature_256: str | None = Header(default=None),
):
    channel = (
        await db.execute(
            select(CustomerChannel).where(
                CustomerChannel.id == channel_id,
                CustomerChannel.channel_type == "whatsapp",
                CustomerChannel.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    raw_body = await request.body()
    config = channel.config or {}
    if not whatsapp_meta_service.verify_webhook_signature(
        raw_body,
        x_hub_signature_256,
        config.get("meta_app_secret"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Meta WhatsApp signature",
        )

    try:
        payload = json.loads(raw_body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON") from exc

    processed = 0
    duplicates = 0
    for message in whatsapp_meta_service.extract_text_messages(payload):
        _, _, duplicate = await _enqueue_whatsapp_message(
            db,
            channel,
            from_phone=message["from_phone"],
            text=message["text"],
            provider_message_id=message.get("message_id") or None,
        )
        if duplicate:
            duplicates += 1
        else:
            processed += 1

    return {"success": True, "processed": processed, "duplicates": duplicates}
