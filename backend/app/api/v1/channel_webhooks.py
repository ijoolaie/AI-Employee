import hashlib
import hmac
from uuid import UUID
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from app.core.deps import DbSession
from app.models.customer_channel import CustomerChannel
from app.services import customer_channel_service
from sqlalchemy import select

router = APIRouter(prefix="/webhooks/channels", tags=["channel-webhooks"])

class WhatsAppInbound(BaseModel):
    from_phone: str = Field(min_length=3, max_length=40)
    text: str = Field(min_length=1, max_length=8000)
    name: str | None = None
    message_id: str | None = None

@router.post("/whatsapp/{channel_id}")
async def whatsapp_inbound(channel_id: UUID, payload: WhatsAppInbound, db: DbSession, x_channel_signature: str | None = Header(default=None)):
    channel = (await db.execute(select(CustomerChannel).where(CustomerChannel.id == channel_id, CustomerChannel.channel_type == "whatsapp", CustomerChannel.is_active.is_(True)))).scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")
    secret = (channel.config or {}).get("webhook_secret")
    if secret:
        expected = hmac.new(secret.encode(), payload.text.encode(), hashlib.sha256).hexdigest()
        if not x_channel_signature or not hmac.compare_digest(expected, x_channel_signature):
            raise HTTPException(status_code=401, detail="Invalid channel signature")
    token = "wa:" + payload.from_phone
    from app.models.conversation import CustomerConversation, CustomerMessage
    existing = (await db.execute(select(CustomerConversation).where(CustomerConversation.channel_id == channel.id, CustomerConversation.customer_phone == payload.from_phone).order_by(CustomerConversation.updated_at.desc()))).scalars().first()
    if not existing:
        customer = await customer_channel_service.customer_service.upsert_customer(db, tenant_id=channel.tenant_id, external_key=payload.from_phone, name=payload.name, phone=payload.from_phone, channel="whatsapp")
        existing = CustomerConversation(tenant_id=channel.tenant_id, employee_id=channel.employee_id, channel_id=channel.id, customer_token_hash=hashlib.sha256(token.encode()).hexdigest(), customer_name=payload.name, customer_phone=payload.from_phone, customer_id=customer.id)
        db.add(existing); await db.flush()
    msg = CustomerMessage(tenant_id=channel.tenant_id, conversation_id=existing.id, role="user", content=payload.text)
    db.add(msg); await db.flush()
    from app.services import run_service
    run = await run_service.create_run(db, tenant_id=channel.tenant_id, employee_id=channel.employee_id, input_data={"message": payload.text, "customer": {"name": existing.customer_name, "phone": payload.from_phone}, "channel": "whatsapp"}, created_by=None, employee_version_id=None)
    run.conversation_id = existing.id
    msg.run_id = run.id
    try:
        from app.workers.run_worker import execute_run_task
        execute_run_task.delay(str(run.id))
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail="Run queue unavailable; retry webhook") from exc
    return {"success": True, "conversation_id": str(existing.id), "run_id": str(run.id), "delivery": "provider_adapter_required"}
