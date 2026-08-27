import hashlib
import secrets
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ConflictError
from app.models.customer_channel import CustomerChannel
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.employee import Employee
from app.models.run import Run
from app.services import employee_service, run_service, customer_service


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

async def create_channel(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID, name: str, channel_type: str, config: dict) -> CustomerChannel:
    employee = await employee_service.get_employee(db, employee_id=employee_id, tenant_id=tenant_id)
    channel = CustomerChannel(tenant_id=tenant_id, employee_id=employee.id, name=name, channel_type=channel_type, public_key="pk_" + secrets.token_urlsafe(24), config=config or {})
    db.add(channel)
    await db.flush(); await db.refresh(channel)
    return channel

async def list_channels(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID | None = None) -> list[CustomerChannel]:
    stmt = select(CustomerChannel).where(CustomerChannel.tenant_id == tenant_id).order_by(CustomerChannel.created_at.desc())
    if employee_id: stmt = stmt.where(CustomerChannel.employee_id == employee_id)
    return list((await db.execute(stmt)).scalars().all())

async def get_public_channel(db: AsyncSession, *, public_key: str) -> tuple[CustomerChannel, Employee]:
    result = await db.execute(select(CustomerChannel, Employee).join(Employee, Employee.id == CustomerChannel.employee_id).where(CustomerChannel.public_key == public_key, CustomerChannel.is_active.is_(True), Employee.is_active.is_(True), Employee.tenant_id == CustomerChannel.tenant_id))
    row = result.first()
    if not row: raise NotFoundError("Public channel not found")
    return row

async def create_conversation(db: AsyncSession, *, public_key: str, customer_name: str | None, customer_email: str | None, customer_phone: str | None) -> tuple[CustomerConversation, str, Employee]:
    channel, employee = await get_public_channel(db, public_key=public_key)
    token = secrets.token_urlsafe(32)
    customer = await customer_service.upsert_customer(db, tenant_id=channel.tenant_id, external_key=customer_phone or customer_email or token[:20], name=customer_name, email=customer_email, phone=customer_phone, channel=channel.channel_type)
    conversation = CustomerConversation(tenant_id=channel.tenant_id, employee_id=employee.id, channel_id=channel.id, customer_token_hash=_hash_token(token), customer_name=customer_name, customer_email=customer_email, customer_phone=customer_phone, customer_id=customer.id)
    db.add(conversation); await db.flush()
    return conversation, token, employee

async def _get_conversation(db: AsyncSession, *, conversation_id: uuid.UUID, token: str) -> CustomerConversation:
    result = await db.execute(select(CustomerConversation).where(CustomerConversation.id == conversation_id, CustomerConversation.customer_token_hash == _hash_token(token)))
    conversation = result.scalar_one_or_none()
    if not conversation: raise NotFoundError("Conversation not found")
    return conversation

async def send_message(db: AsyncSession, *, conversation_id: uuid.UUID, token: str, content: str):
    conversation = await _get_conversation(db, conversation_id=conversation_id, token=token)
    active = (await db.execute(select(func.count()).select_from(Run).where(Run.conversation_id == conversation.id, Run.tenant_id == conversation.tenant_id, Run.status.in_(["pending", "running"])))).scalar_one()
    if active:
        raise ConflictError("Please wait for the current assistant response before sending another message")
    message = CustomerMessage(tenant_id=conversation.tenant_id, conversation_id=conversation.id, role="user", content=content)
    db.add(message); await db.flush()
    run = await run_service.create_run(db, tenant_id=conversation.tenant_id, employee_id=conversation.employee_id, input_data={"message": content, "customer": {"name": conversation.customer_name, "email": conversation.customer_email, "phone": conversation.customer_phone}, "channel": "web_widget"}, created_by=None, employee_version_id=None)
    run.conversation_id = conversation.id
    message.run_id = run.id
    try:
        from app.workers.run_worker import execute_run_task
        execute_run_task.delay(str(run.id))
    except Exception as exc:
        await db.rollback()
        raise RuntimeError("Run queue unavailable; retry message") from exc
    return conversation, run

async def get_public_conversation(db: AsyncSession, *, conversation_id: uuid.UUID, token: str) -> tuple[CustomerConversation, Employee, list[CustomerMessage]]:
    conversation = await _get_conversation(db, conversation_id=conversation_id, token=token)
    employee = (await db.execute(select(Employee).where(Employee.id == conversation.employee_id, Employee.tenant_id == conversation.tenant_id))).scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee not found")
    messages = list((await db.execute(select(CustomerMessage).where(CustomerMessage.conversation_id == conversation.id, CustomerMessage.tenant_id == conversation.tenant_id).order_by(CustomerMessage.created_at.asc()))).scalars().all())
    return conversation, employee, messages

async def list_conversations(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID | None = None) -> list[dict]:
    stmt = select(CustomerConversation).where(CustomerConversation.tenant_id == tenant_id).order_by(CustomerConversation.updated_at.desc())
    if employee_id: stmt = stmt.where(CustomerConversation.employee_id == employee_id)
    conversations = list((await db.execute(stmt)).scalars().all())
    out=[]
    for c in conversations:
        messages=list((await db.execute(select(CustomerMessage).where(CustomerMessage.conversation_id==c.id, CustomerMessage.tenant_id == c.tenant_id).order_by(CustomerMessage.created_at.desc()).limit(1))).scalars().all())
        count=(await db.execute(select(func.count(CustomerMessage.id)).where(CustomerMessage.conversation_id==c.id, CustomerMessage.tenant_id == c.tenant_id))).scalar_one()
        out.append({"id":c.id,"employee_id":c.employee_id,"channel_id":c.channel_id,"status":c.status,"customer_name":c.customer_name,"customer_email":c.customer_email,"customer_phone":c.customer_phone,"message_count":count,"last_message":messages[0].content if messages else None,"updated_at":c.updated_at})
    return out


async def update_handoff(db: AsyncSession, *, tenant_id: uuid.UUID, conversation_id: uuid.UUID, requested: bool, assigned_user_id: uuid.UUID | None):
    conversation = (await db.execute(select(CustomerConversation).where(CustomerConversation.id == conversation_id, CustomerConversation.tenant_id == tenant_id))).scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    conversation.handoff_requested = requested
    conversation.assigned_user_id = assigned_user_id if requested else None
    conversation.status = "human" if requested else "open"
    await db.flush(); await db.refresh(conversation)
    return conversation
