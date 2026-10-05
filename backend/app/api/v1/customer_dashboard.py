from uuid import UUID

from fastapi import APIRouter

from app.core.deps import AuditReadContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.customer_dashboard import (
    CustomerCareerResponse,
    CustomerDashboardResponse,
    CustomerOfficeResponse,
    CustomerMeetingResponse,
)
from app.services import customer_dashboard_service

router = APIRouter(prefix='/customer-dashboard', tags=['customer-dashboard'])

@router.get('/meetings/{meeting_id}', response_model=APIResponse[CustomerMeetingResponse])
async def get_customer_meeting(meeting_id: UUID, ctx: AuditReadContext, db: DbSession):
    from app.services import meeting_service
    meeting = await meeting_service.get_meeting(db, tenant_id=ctx.tenant_id, meeting_id=meeting_id)
    return APIResponse(success=True, data=meeting)

@router.get('/office', response_model=APIResponse[CustomerOfficeResponse])
async def get_customer_office(ctx: AuditReadContext, db: DbSession):
    office = await customer_dashboard_service.get_office(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=office)

@router.get('', response_model=APIResponse[CustomerDashboardResponse])
async def get_customer_dashboard(ctx: AuditReadContext, db: DbSession):
    data = await customer_dashboard_service.get_dashboard(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=CustomerDashboardResponse.model_validate(data))


@router.get(
    "/employees/{employee_id}/career",
    response_model=APIResponse[CustomerCareerResponse],
)
async def get_employee_career(
    employee_id: UUID,
    ctx: AuditReadContext,
    db: DbSession,
):
    career = await customer_dashboard_service.get_employee_career(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
    )
    return APIResponse(success=True, data=career)
