from uuid import UUID
from fastapi import APIRouter, Header
from app.core.deps import DbSession
from app.schemas.common import APIResponse
from app.schemas.customer_channel import PublicChannelResponse, PublicConversationCreate, PublicConversationResponse, PublicMessageCreate, PublicMessageResponse
from app.services import customer_channel_service

router = APIRouter(prefix="/public/chat", tags=["public-chat"])

@router.get("/channels/{public_key}", response_model=APIResponse[PublicChannelResponse])
async def get_channel(public_key: str, db: DbSession):
    channel, employee = await customer_channel_service.get_public_channel(db, public_key=public_key)
    return APIResponse(success=True, data=PublicChannelResponse(public_key=channel.public_key, employee_id=employee.id, employee_name=employee.name, employee_slug=employee.slug, channel_name=channel.name, channel_type=channel.channel_type, config=channel.config))

@router.post("/channels/{public_key}/conversations", response_model=APIResponse[PublicConversationResponse])
async def create_conversation(public_key: str, payload: PublicConversationCreate, db: DbSession):
    conversation, token, employee = await customer_channel_service.create_conversation(db, public_key=public_key, customer_name=payload.customer_name, customer_email=payload.customer_email, customer_phone=payload.customer_phone)
    return APIResponse(success=True, data=PublicConversationResponse(id=conversation.id, employee_name=employee.name, status=conversation.status, customer_token=token, messages=[]))

@router.get("/conversations/{conversation_id}", response_model=APIResponse[PublicConversationResponse])
async def get_conversation(conversation_id: UUID, db: DbSession, x_customer_token: str = Header(...)):
    conversation, employee, messages = await customer_channel_service.get_public_conversation(db, conversation_id=conversation_id, token=x_customer_token)
    return APIResponse(success=True, data=PublicConversationResponse(id=conversation.id, employee_name=employee.name, status=conversation.status, messages=[PublicMessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in messages]))

@router.post("/conversations/{conversation_id}/messages", response_model=APIResponse[dict])
async def send_message(conversation_id: UUID, payload: PublicMessageCreate, db: DbSession, x_customer_token: str = Header(...)):
    conversation, run = await customer_channel_service.send_message(db, conversation_id=conversation_id, token=x_customer_token, content=payload.content.strip())
    return APIResponse(success=True, data={"conversation_id": conversation.id, "run_id": run.id, "status": run.status})
