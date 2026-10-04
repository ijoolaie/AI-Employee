"""Employee endpoints (11_Employee_Framework). Tenant users can only create
Custom Employees; System Employees (tenant_id NULL) are seeded/managed by
the platform team, not through this router."""

from uuid import UUID

from fastapi import APIRouter, status

from app.ai.tool_registry import registry

from app.core.deps import CurrentContext, DbSession, EmployeeReadContext, EmployeeWriteContext
from app.schemas.common import APIResponse
from app.schemas.skill_marketplace import SkillInstallationResponse
from app.schemas.employee import (
    EmployeeCreate,
    EmployeePresentationProfile,
    EmployeePresentationProfileUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    EmployeeVersionCreate,
    EmployeeVersionResponse,
    ToolResponse,
)
from app.services import employee_service
from app.services import cosmetic_entitlement_service
from app.services import skill_marketplace_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=APIResponse[EmployeeResponse], status_code=status.HTTP_201_CREATED)
async def create_employee(payload: EmployeeCreate, ctx: EmployeeWriteContext, db: DbSession):
    employee = await employee_service.create_employee(
        db,
        tenant_id=ctx.tenant_id,
        slug=payload.slug,
        name=payload.name,
        avatar_url=payload.avatar_url,
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


@router.put(
    "/{employee_id}/presentation",
    response_model=APIResponse[EmployeeResponse],
)
async def update_presentation(
    employee_id: UUID,
    payload: EmployeePresentationProfileUpdate,
    ctx: EmployeeWriteContext,
    db: DbSession,
):
    employee = await employee_service.update_presentation_profile(
        db,
        employee_id=employee_id,
        tenant_id=ctx.tenant_id,
        presentation_profile=payload.model_dump(),
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=EmployeeResponse.model_validate(employee))


@router.post(
    "/{employee_id}/cosmetics/{product_id}/apply",
    response_model=APIResponse[EmployeeResponse],
)
async def apply_cosmetic(
    employee_id: UUID,
    product_id: UUID,
    ctx: EmployeeWriteContext,
    db: DbSession,
):
    employee = await cosmetic_entitlement_service.apply_entitlement(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
        product_id=product_id,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=EmployeeResponse.model_validate(employee))


@router.post(
    "/{employee_id}/skills/{skill_package_id}",
    response_model=APIResponse[SkillInstallationResponse],
)
async def install_skill(
    employee_id: UUID,
    skill_package_id: UUID,
    ctx: EmployeeWriteContext,
    db: DbSession,
):
    installation = await skill_marketplace_service.install(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
        skill_package_id=skill_package_id,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=SkillInstallationResponse.model_validate(installation))


@router.delete(
    "/{employee_id}/skills/{skill_package_id}",
    response_model=APIResponse[SkillInstallationResponse],
)
async def revoke_skill(
    employee_id: UUID,
    skill_package_id: UUID,
    ctx: EmployeeWriteContext,
    db: DbSession,
):
    installation = await skill_marketplace_service.revoke(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
        skill_package_id=skill_package_id,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=SkillInstallationResponse.model_validate(installation))


@router.get(
    "/{employee_id}/skills",
    response_model=APIResponse[list[SkillInstallationResponse]],
)
async def list_skills(
    employee_id: UUID,
    ctx: EmployeeReadContext,
    db: DbSession,
):
    installations = await skill_marketplace_service.list_for_employee(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=employee_id,
        active_only=True,
    )
    return APIResponse(
        success=True,
        data=[SkillInstallationResponse.model_validate(item) for item in installations],
    )


@router.post(
    "/{employee_id}/status",
    response_model=APIResponse[EmployeeResponse],
)
async def update_status(
    employee_id: UUID,
    payload: EmployeeStatusUpdate,
    ctx: EmployeeWriteContext,
    db: DbSession,
):
    employee = await employee_service.set_employee_status(
        db,
        employee_id=employee_id,
        tenant_id=ctx.tenant_id,
        is_active=payload.is_active,
        actor_id=ctx.user_id,
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
