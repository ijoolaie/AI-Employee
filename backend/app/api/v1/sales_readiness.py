from uuid import UUID
from fastapi import APIRouter
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.sales_readiness import EmployeeTemplate, GuardrailsResponse, GuardrailsUpdate, AnalyticsResponse, PrivacyExport
from app.services import sales_readiness_service

router=APIRouter(tags=["sales-readiness"])

@router.get("/employee-templates", response_model=APIResponse[list[EmployeeTemplate]])
async def templates(ctx: CurrentContext):
    return APIResponse(success=True,data=[EmployeeTemplate(**x) for x in sales_readiness_service.list_templates()])

@router.post("/employee-templates/{code}/install", response_model=APIResponse[dict])
async def install_template(code: str, ctx: CurrentContext, db: DbSession):
    e=await sales_readiness_service.create_from_template(db,tenant_id=ctx.tenant_id,actor_id=ctx.user_id,code=code)
    return APIResponse(success=True,data={"id":str(e.id),"name":e.name,"slug":e.slug})

@router.get("/employees/{employee_id}/guardrails", response_model=APIResponse[GuardrailsResponse])
async def get_guardrails(employee_id: UUID, ctx: CurrentContext, db: DbSession):
    e,v=await sales_readiness_service.get_guardrails(db,tenant_id=ctx.tenant_id,employee_id=employee_id)
    return APIResponse(success=True,data=GuardrailsResponse(employee_id=e.id,version_id=v.id,rules=v.rules or {}))

@router.put("/employees/{employee_id}/guardrails", response_model=APIResponse[GuardrailsResponse])
async def put_guardrails(employee_id: UUID,payload: GuardrailsUpdate,ctx: CurrentContext,db: DbSession):
    v=await sales_readiness_service.update_guardrails(db,tenant_id=ctx.tenant_id,employee_id=employee_id,actor_id=ctx.user_id,rules=payload.rules,allowed_tools=payload.allowed_tools)
    return APIResponse(success=True,data=GuardrailsResponse(employee_id=employee_id,version_id=v.id,rules=v.rules or {}))

@router.get("/analytics/roi", response_model=APIResponse[AnalyticsResponse])
async def roi(ctx: CurrentContext, db: DbSession):
    return APIResponse(success=True,data=AnalyticsResponse(**(await sales_readiness_service.analytics(db,tenant_id=ctx.tenant_id))))

@router.get("/privacy/customers/{customer_id}/export", response_model=APIResponse[PrivacyExport])
async def export_customer(customer_id: UUID,ctx: CurrentContext,db: DbSession):
    return APIResponse(success=True,data=PrivacyExport(**(await sales_readiness_service.export_customer(db,tenant_id=ctx.tenant_id,customer_id=customer_id))))

@router.delete("/privacy/customers/{customer_id}", response_model=APIResponse[dict])
async def delete_customer(customer_id: UUID,ctx: CurrentContext,db: DbSession):
    return APIResponse(success=True,data=await sales_readiness_service.delete_customer(db,tenant_id=ctx.tenant_id,customer_id=customer_id,actor_id=ctx.user_id))
