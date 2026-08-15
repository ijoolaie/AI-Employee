from uuid import UUID
from fastapi import APIRouter, status
from app.core.deps import DbSession, EmployeeReadContext, EmployeeWriteContext
from app.schemas.common import APIResponse
from app.schemas.customer_channel import CustomerChannelCreate, CustomerChannelResponse, CustomerConversationSummary
from app.services import customer_channel_service

router = APIRouter(prefix="/customer-channels", tags=["customer-channels"])

@router.post("", response_model=APIResponse[CustomerChannelResponse], status_code=status.HTTP_201_CREATED)
async def create_channel(payload: CustomerChannelCreate, ctx: EmployeeWriteContext, db: DbSession):
    channel = await customer_channel_service.create_channel(db, tenant_id=ctx.tenant_id, employee_id=payload.employee_id, name=payload.name, channel_type=payload.channel_type, config=payload.config)
    return APIResponse(success=True, data=CustomerChannelResponse.model_validate(channel))

@router.get("", response_model=APIResponse[list[CustomerChannelResponse]])
async def list_channels(ctx: EmployeeReadContext, db: DbSession, employee_id: UUID | None = None):
    channels = await customer_channel_service.list_channels(db, tenant_id=ctx.tenant_id, employee_id=employee_id)
    return APIResponse(success=True, data=[CustomerChannelResponse.model_validate(c) for c in channels])

@router.get("/conversations", response_model=APIResponse[list[CustomerConversationSummary]])
async def list_conversations(ctx: EmployeeReadContext, db: DbSession, employee_id: UUID | None = None):
    items = await customer_channel_service.list_conversations(db, tenant_id=ctx.tenant_id, employee_id=employee_id)
    return APIResponse(success=True, data=[CustomerConversationSummary.model_validate(i) for i in items])
