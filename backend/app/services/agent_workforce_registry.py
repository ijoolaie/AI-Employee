"""Tenant-scoped read model for the governed Agent workforce.

The registry intentionally preserves the Stage 8 identity boundary:
AgentDefinition -> AgentTemplate -> AgentInstance. It is a projection only;
it does not create or mutate governance records.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate
from app.models.run import Run


def _tools(instance: AgentInstance, template: AgentTemplate | None, definition: AgentDefinition) -> list[str]:
    policy = instance.permission_policy or {}
    configured = policy.get("allowed_tools") or policy.get("tools")
    if configured is not None:
        return sorted({str(item) for item in configured})
    if template is not None:
        configured = template.permission_policy.get("allowed_tools") or template.permission_policy.get("tools")
        if configured is not None:
            return sorted({str(item) for item in configured})
    return sorted({str(item) for item in (definition.allowed_tools or [])})


async def list_workforce(
    db: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[dict[str, Any]]:
    """Return every tenant Agent instance with its governance projection."""
    cost_subquery = (
        select(
            Run.agent_instance_id.label("agent_instance_id"),
            func.coalesce(func.sum(Run.total_cost_usd), 0).label("total_cost_usd"),
            func.max(Run.created_at).label("last_run_at"),
        )
        .where(Run.tenant_id == tenant_id, Run.agent_instance_id.is_not(None))
        .group_by(Run.agent_instance_id)
        .subquery()
    )

    query = (
        select(AgentInstance, AgentDefinition, AgentTemplate, AgentIdentity,
               cost_subquery.c.total_cost_usd, cost_subquery.c.last_run_at)
        .join(
            AgentDefinition,
            (AgentDefinition.id == AgentInstance.agent_definition_id)
            & (AgentDefinition.tenant_id == tenant_id),
        )
        .outerjoin(
            AgentTemplate,
            (AgentTemplate.id == AgentInstance.agent_template_id)
            & (AgentTemplate.tenant_id == tenant_id),
        )
        .outerjoin(
            AgentIdentity,
            (AgentIdentity.agent_instance_id == AgentInstance.id)
            & (AgentIdentity.tenant_id == tenant_id),
        )
        .outerjoin(cost_subquery, cost_subquery.c.agent_instance_id == AgentInstance.id)
        .where(AgentInstance.tenant_id == tenant_id)
        .order_by(AgentInstance.created_at.desc())
    )

    result = await db.execute(query)
    rows: list[dict[str, Any]] = []
    for instance, definition, template, identity, total_cost_usd, last_run_at in result.all():
        budget = instance.budget_policy or {}
        rows.append(
            {
                "agent_instance_id": instance.id,
                "agent_definition_id": definition.id,
                "agent_template_id": template.id if template is not None else None,
                "name": instance.name,
                "definition": {
                    "slug": definition.slug,
                    "name": definition.name,
                    "version": definition.version,
                    "enabled": definition.enabled,
                },
                "template": {
                    "slug": template.slug,
                    "name": template.name,
                    "version": template.version,
                    "status": template.status.value,
                } if template is not None else None,
                "status": instance.status.value,
                "enabled": instance.enabled,
                "risk_tier": instance.risk_tier,
                "owner_user_id": identity.owner_user_id if identity is not None else None,
                "sponsor_user_id": identity.sponsor_user_id if identity is not None else instance.sponsor_user_id,
                "identity_id": identity.id if identity is not None else None,
                "identity_active": identity.active if identity is not None else False,
                "identity_expires_at": identity.expires_at if identity is not None else None,
                "identity_revoked_at": identity.revoked_at if identity is not None else None,
                "tools": _tools(instance, template, definition),
                "capabilities": definition.capabilities or [],
                "max_concurrency": instance.max_concurrency,
                "budget_policy": budget,
                "total_cost_usd": float(Decimal(total_cost_usd or 0)),
                "last_run_at": last_run_at,
            }
        )
    return rows
