from uuid import UUID
from fastapi import APIRouter
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.inbox import HandoffUpdate, InboxConversationResponse, InboxMessageCreate
from app.services import customer_channel_service

router = APIRouter(prefix="/inbox", tags=["inbox"])

@router.get("/conversations", response_model=APIResponse[list[InboxConversationResponse]])
async def inbox(ctx: CurrentContext, db: DbSession):
    rows = await customer_channel_service.list_conversations(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[InboxConversationResponse(handoff_requested=(await _handoff(db, x["id"], ctx.tenant_id)), assigned_user_id=await _assigned(db, x["id"], ctx.tenant_id), **x) for x in rows])

async def _handoff(db, cid, tenant_id):
    from sqlalchemy import select
    from app.models.conversation import CustomerConversation
    return (await db.execute(select(CustomerConversation.handoff_requested).where(CustomerConversation.id == cid, CustomerConversation.tenant_id == tenant_id))).scalar_one()

async def _assigned(db, cid, tenant_id):
    from sqlalchemy import select
    from app.models.conversation import CustomerConversation
    return (await db.execute(select(CustomerConversation.assigned_user_id).where(CustomerConversation.id == cid, CustomerConversation.tenant_id == tenant_id))).scalar_one()

@router.post("/conversations/{conversation_id}/handoff", response_model=APIResponse[dict])
async def handoff(conversation_id: UUID, payload: HandoffUpdate, ctx: CurrentContext, db: DbSession):
    row = await customer_channel_service.update_handoff(db, tenant_id=ctx.tenant_id, conversation_id=conversation_id, requested=payload.requested, assigned_user_id=payload.assigned_user_id)
    return APIResponse(success=True, data={"id": str(row.id), "status": row.status, "handoff_requested": row.handoff_requested, "assigned_user_id": str(row.assigned_user_id) if row.assigned_user_id else None})

@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse[list[dict]])
async def inbox_messages(conversation_id: UUID, ctx: CurrentContext, db: DbSession):
    from sqlalchemy import select
    from app.models.conversation import CustomerConversation, CustomerMessage
    exists = (await db.execute(select(CustomerConversation.id).where(CustomerConversation.id == conversation_id, CustomerConversation.tenant_id == ctx.tenant_id))).scalar_one_or_none()
    if not exists:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Conversation not found")
    rows = (await db.execute(select(CustomerMessage).where(CustomerMessage.conversation_id == conversation_id, CustomerMessage.tenant_id == ctx.tenant_id).order_by(CustomerMessage.created_at.asc()))).scalars().all()
    return APIResponse(success=True, data=[{"id": str(r.id), "role": r.role, "content": r.content, "created_at": r.created_at} for r in rows])

@router.post("/conversations/{conversation_id}/messages", response_model=APIResponse[dict])
async def inbox_send_message(conversation_id: UUID, payload: InboxMessageCreate, ctx: CurrentContext, db: DbSession):
    from sqlalchemy import select
    from app.models.conversation import CustomerConversation, CustomerMessage
    conversation = (await db.execute(select(CustomerConversation).where(CustomerConversation.id == conversation_id, CustomerConversation.tenant_id == ctx.tenant_id))).scalar_one_or_none()
    if not conversation:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Conversation not found")
    conversation.handoff_requested = True
    conversation.status = "human"
    message = CustomerMessage(tenant_id=ctx.tenant_id, conversation_id=conversation.id, role="human", content=payload.content.strip())
    db.add(message)
    await db.flush(); await db.refresh(message)
    return APIResponse(success=True, data={"id": str(message.id), "conversation_id": str(conversation.id), "role": "human", "content": message.content, "created_at": message.created_at})
