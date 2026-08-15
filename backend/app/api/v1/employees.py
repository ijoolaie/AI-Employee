"""Employee endpoints (11_Employee_Framework). Tenant users can only create
Custom Employees; System Employees (tenant_id NULL) are seeded/managed by
the platform team, not through this router."""

from uuid import UUID

from fastapi import APIRouter, status

from app.ai.tool_registry import registry

from app.core.deps import CurrentContext, DbSession, EmployeeReadContext, EmployeeWriteContext
from app.schemas.common import APIResponse
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeVersionCreate,
    EmployeeVersionResponse,
    ToolResponse,
)
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=APIResponse[EmployeeResponse], status_code=status.HTTP_201_CREATED)
async def create_employee(payload: EmployeeCreate, ctx: EmployeeWriteContext, db: DbSession):
    employee = await employee_service.create_employee(
        db,
        tenant_id=ctx.tenant_id,
        slug=payload.slug,
        name=payload.name,
        kind=payload.kind,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        prompt_template=payload.prompt_template,
        allowed_tools=payload.allowed_tools,
        rules=payload.rules,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=EmployeeResponse.model_validate(employee))


@router.get("", response_model=APIResponse[list[EmployeeResponse]])
async def list_employees(ctx: EmployeeReadContext, db: DbSession):
    employees = await employee_service.list_employees(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[EmployeeResponse.model_validate(e) for e in employees])



@router.get("/available-tools", response_model=APIResponse[list[ToolResponse]])
async def list_available_tools(ctx: EmployeeReadContext):
    """List registered tools and their JSON Schemas. Execution is internal to Run."""
    tools = [
        ToolResponse(
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            side_effects=tool.side_effects,
            required_permission=tool.required_permission,
            requires_approval=tool.requires_approval,
        )
        for tool in registry.list()
    ]
    return APIResponse(success=True, data=tools)

@router.get("/{employee_id}", response_model=APIResponse[EmployeeResponse])
async def get_employee(employee_id: UUID, ctx: EmployeeReadContext, db: DbSession):
    employee = await employee_service.get_employee(
        db, employee_id=employee_id, tenant_id=ctx.tenant_id
    )
    return APIResponse(success=True, data=EmployeeResponse.model_validate(employee))


@router.post(
    "/{employee_id}/versions",
    response_model=APIResponse[EmployeeVersionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    employee_id: UUID, payload: EmployeeVersionCreate, ctx: EmployeeWriteContext, db: DbSession
):
    version = await employee_service.publish_new_version(
        db,
        employee_id=employee_id,
        tenant_id=ctx.tenant_id,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        prompt_template=payload.prompt_template,
        allowed_tools=payload.allowed_tools,
        rules=payload.rules,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=EmployeeVersionResponse.model_validate(version))
