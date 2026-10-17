"""Read-only first-party AI Company workforce role and template catalog."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.agent_definition import AgentDefinition
from app.models.agent_template import AgentTemplate
from app.services.audit_service import record
from app.services.workforce_template_materialization import create_first_party_workforce_template
from app.services.ai_workforce_roles import get_workforce_role, get_workforce_role_template, list_workforce_role_templates, list_workforce_roles

router = APIRouter(prefix="/ai-workforce-roles", tags=["ai-workforce-roles"])


@router.get("")
async def get_ai_workforce_roles(
    _ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
) -> list[dict]:
    """Return the governed first-party role catalog without provisioning anything."""
    return list_workforce_roles()


@router.get("/templates")
async def get_ai_workforce_role_templates(
    _ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
) -> list[dict]:
    """Return the first-party workforce role templates without provisioning anything."""
    return list_workforce_role_templates()



@router.post("/templates/{role_code}/materialize", status_code=status.HTTP_201_CREATED)
async def materialize_first_party_workforce_template(
    role_code: str,
    ctx: TenantContext = Depends(require_permission("agent_template.create")),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict:
    """Create a tenant-scoped DRAFT template from the canonical first-party role catalog.

    This endpoint deliberately does not evaluate, publish, provision, or activate
    an agent. Role capabilities are sourced server-side and never accepted from
    the request body.
    """
    try:
        role = get_workforce_role(role_code)
        role_template = get_workforce_role_template(role_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="First-party workforce role not found") from exc

    existing = (await db.execute(
        select(AgentTemplate).where(
            AgentTemplate.tenant_id == ctx.tenant_id,
            AgentTemplate.slug == role_template.slug,
            AgentTemplate.version == 1,
        )
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="First-party workforce template version already exists")

    try:
        definition = (await db.execute(
            select(AgentDefinition).where(
                AgentDefinition.tenant_id == ctx.tenant_id,
                AgentDefinition.slug == role_template.slug,
            )
        )).scalar_one_or_none()
        if definition is None:
            all_contracts = list(role.capability_contract)
            allowed_tools = sorted({tool for contract in all_contracts for tool in contract.tool_names})
            definition = AgentDefinition(
                tenant_id=ctx.tenant_id,
                slug=role_template.slug,
                name=role_template.name,
                description=role_template.description,
                version=1,
                capabilities=list(role.allowed_routine_operations) + list(role.approval_required_operations),
                allowed_tools=allowed_tools,
                model_policy={},
                input_schema={},
                output_schema={},
                policy_requirements={
                    "workforce_role_code": role.code,
                    "workforce_capability_contract": [
                        {
                            "operation": contract.operation,
                            "capability_code": contract.capability_code,
                            "tool_names": list(contract.tool_names),
                            "required_permissions": list(contract.required_permissions),
                            "approval_required": contract.approval_required,
                        }
                        for contract in all_contracts
                    ],
                },
                enabled=True,
            )
            db.add(definition)
            await db.flush()
        else:
            # Never silently rebind an existing tenant definition with a mismatched
            # slug/name/role contract to a first-party workforce template.
            expected_capabilities = list(role.allowed_routine_operations) + list(role.approval_required_operations)
            expected_tools = sorted({tool for contract in role.capability_contract for tool in contract.tool_names})
            if (
                definition.name != role_template.name
                or definition.capabilities != expected_capabilities
                or sorted(definition.allowed_tools or []) != expected_tools
                or (definition.policy_requirements or {}).get("workforce_role_code") != role.code
            ):
                raise HTTPException(status_code=409, detail="Existing tenant AgentDefinition conflicts with the first-party role")

        item = await create_first_party_workforce_template(
            db,
            tenant_id=ctx.tenant_id,
            agent_definition_id=definition.id,
            role_code=role_code,
            version=1,
            risk_tier=2,
            permission_policy={"permissions": ["run.execute"], "allowed_tools": list(definition.allowed_tools)},
            approval_policy={"requires_human_approval_for_sensitive_operations": True},
            evaluation_policy={"requires_evidence": True},
            install_policy={"requires_ceo_approval": True},
            name=role_template.name,
            description=role_template.description,
        )
        await record(
            db,
            action="agent_template.first_party_materialized",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="agent_template",
            resource_id=item.id,
            metadata={"role_code": role_code, "version": item.version, "status": item.status.value},
        )
        await db.commit()
        await db.refresh(item)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Could not materialize the first-party workforce template") from exc

    return {
        "id": str(item.id),
        "agent_definition_id": str(item.agent_definition_id),
        "slug": item.slug,
        "name": item.name,
        "version": item.version,
        "status": item.status.value,
        "role_code": role_code,
        "next_step": "evaluation_required",
    }
