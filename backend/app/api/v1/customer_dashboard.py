from fastapi import APIRouter
from app.core.deps import AuditReadContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.customer_dashboard import CustomerCareerResponse, CustomerDashboardResponse, CustomerOfficeResponse
from app.services import customer_dashboard_service

router = APIRouter(prefix='/customer-dashboard', tags=['customer-dashboard'])

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
    employee_id: str,
    ctx: AuditReadContext,
    db: DbSession,
):
    career = await customer_dashboard_service.get_employee_career(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
    )
    return APIResponse(success=True, data=career)
