from uuid import UUID
from fastapi import APIRouter, Header
from app.core.deps import DbSession
from app.schemas.common import APIResponse
from app.schemas.customer_channel import PublicChannelResponse, PublicConversationCreate, PublicConversationResponse, PublicMessageCreate, PublicMessageResponse, PublicEmailVerificationCode, PublicEmailVerificationResponse, PublicCustomerOrdersResponse
from app.services import customer_channel_service

router = APIRouter(prefix="/public/chat", tags=["public-chat"])

@router.get("/channels/{public_key}", response_model=APIResponse[PublicChannelResponse])
async def get_channel(public_key: str, db: DbSession):
    channel, employee = await customer_channel_service.get_public_channel(db, public_key=public_key)
    # Channel config is tenant-owned and may contain credentials (for example,
    # WhatsApp webhook_secret). The public widget does not need it, so never
    # serialize private channel configuration through this unauthenticated API.
    return APIResponse(success=True, data=PublicChannelResponse(public_key=channel.public_key, employee_id=employee.id, employee_name=employee.name, employee_slug=employee.slug, channel_name=channel.name, channel_type=channel.channel_type, config={}))

@router.post("/channels/{public_key}/conversations", response_model=APIResponse[PublicConversationResponse])
async def create_conversation(public_key: str, payload: PublicConversationCreate, db: DbSession):
    conversation, token, employee = await customer_channel_service.create_conversation(db, public_key=public_key, customer_name=payload.customer_name, customer_email=payload.customer_email, customer_phone=payload.customer_phone)
    employee_name = employee.name
    await db.commit()
    await db.refresh(conversation)
    return APIResponse(success=True, data=PublicConversationResponse(id=conversation.id, employee_name=employee_name, status=conversation.status, customer_token=token, email_verified=False, messages=[]))

@router.get("/conversations/{conversation_id}", response_model=APIResponse[PublicConversationResponse])
async def get_conversation(conversation_id: UUID, db: DbSession, x_customer_token: str = Header(...)):
    conversation, employee, messages = await customer_channel_service.get_public_conversation(db, conversation_id=conversation_id, token=x_customer_token)
    return APIResponse(success=True, data=PublicConversationResponse(id=conversation.id, employee_name=employee.name, status=conversation.status, email_verified=conversation.email_verified_at is not None, messages=[PublicMessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in messages]))

@router.post("/conversations/{conversation_id}/messages", response_model=APIResponse[dict])
async def send_message(conversation_id: UUID, payload: PublicMessageCreate, db: DbSession, x_customer_token: str = Header(...)):
    conversation, run = await customer_channel_service.send_message(db, conversation_id=conversation_id, token=x_customer_token, content=payload.content.strip())
    return APIResponse(success=True, data={"conversation_id": conversation.id, "run_id": run.id if run is not None else None, "status": run.status if run is not None else conversation.status})



@router.post("/conversations/{conversation_id}/email-verification", response_model=APIResponse[dict])
async def request_email_verification(conversation_id: UUID, db: DbSession, x_customer_token: str = Header(...)):
    await customer_channel_service.request_customer_email_verification(
        db, conversation_id=conversation_id, token=x_customer_token
    )
    await db.commit()
    return APIResponse(success=True, data={"message": "If email verification is available, a code has been sent."})


@router.post("/conversations/{conversation_id}/email-verification/confirm", response_model=APIResponse[PublicEmailVerificationResponse])
async def confirm_email_verification(conversation_id: UUID, payload: PublicEmailVerificationCode, db: DbSession, x_customer_token: str = Header(...)):
    verified = await customer_channel_service.verify_customer_email(
        db, conversation_id=conversation_id, token=x_customer_token, code=payload.code
    )
    await db.commit()
    return APIResponse(success=True, data=PublicEmailVerificationResponse(
        verified=verified,
        message="Email verified." if verified else "The code is invalid or expired."
    ))



@router.get("/conversations/{conversation_id}/orders", response_model=APIResponse[PublicCustomerOrdersResponse])
async def get_customer_orders(conversation_id: UUID, db: DbSession, x_customer_token: str = Header(...)):
    data = await customer_channel_service.get_public_customer_orders(
        db, conversation_id=conversation_id, token=x_customer_token
    )
    return APIResponse(success=True, data=PublicCustomerOrdersResponse.model_validate(data))
