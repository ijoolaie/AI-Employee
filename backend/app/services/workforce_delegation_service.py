"""CEO-controlled, durable delegation for the AI Internal Manager."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate
from app.models.workforce_delegation import WorkforceDelegation
from app.services.audit_service import record

MAX_DELEGATION_DAYS = 365
MANAGER_TEMPLATE_SLUG = "ai-internal-manager"

ALLOWED_MANAGER_OPERATIONS = frozenset({
    "assign_task", "reprioritize_task", "coordinate_handoff", "balance_workload",
    "request_workforce_capacity", "prepare_ceo_report", "prepare_budget_estimate",
    "prepare_cost_optimization", "staffing_proposal", "replacement_proposal",
    "transfer_proposal", "retirement_proposal",
})


async def _get_manager(db: AsyncSession, *, tenant_id: UUID, manager_agent_instance_id: UUID) -> AgentInstance:
    result = await db.execute(
        select(AgentInstance)
        .join(AgentTemplate, AgentTemplate.id == AgentInstance.agent_template_id)
        .where(
            AgentInstance.id == manager_agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
            AgentTemplate.tenant_id == tenant_id,
            AgentTemplate.slug == MANAGER_TEMPLATE_SLUG,
        )
    )
    manager = result.scalar_one_or_none()
    if manager is None:
        raise NotFoundError("AI Internal Manager instance not found for tenant")
    if not manager.enabled or manager.status is not AgentInstanceStatus.ENABLED:
        raise ConflictError("AI Internal Manager instance is not active")
    return manager


async def create_delegation(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    manager_agent_instance_id: UUID,
    delegated_by_user_id: UUID,
    starts_at: datetime,
    expires_at: datetime,
    allowed_operations: list[str],
    affected_employee_ids: list[str] | None = None,
    scope: dict | None = None,
    resource_limits: dict | None = None,
    risk_tier: int = 0,
    revocation_conditions: list[str] | None = None,
) -> WorkforceDelegation:
    now = datetime.now(timezone.utc)
    if starts_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValidationAppError("Delegation timestamps must include timezone")
    if expires_at <= starts_at:
        raise ValidationAppError("Delegation expires_at must be after starts_at")
    if expires_at > starts_at + timedelta(days=MAX_DELEGATION_DAYS):
        raise ValidationAppError("Delegation duration exceeds maximum")
    if not 0 <= risk_tier <= 4:
        raise ValidationAppError("risk_tier must be between 0 and 4")
    unknown = set(allowed_operations) - ALLOWED_MANAGER_OPERATIONS
    if unknown:
        raise ValidationAppError(f"Unsupported manager delegation operations: {sorted(unknown)}")
    if not allowed_operations:
        raise ValidationAppError("At least one delegated operation is required")
    await _get_manager(db, tenant_id=tenant_id, manager_agent_instance_id=manager_agent_instance_id)
    delegation = WorkforceDelegation(
        tenant_id=tenant_id,
        manager_agent_instance_id=manager_agent_instance_id,
        delegated_by_user_id=delegated_by_user_id,
        scope=scope or {},
        affected_employee_ids=affected_employee_ids or [],
        allowed_operations=sorted(set(allowed_operations)),
        resource_limits=resource_limits or {},
        risk_tier=risk_tier,
        status="active" if starts_at <= now < expires_at else "scheduled",
        starts_at=starts_at,
        expires_at=expires_at,
        revocation_conditions=revocation_conditions or [],
    )
    db.add(delegation)
    await db.flush()
    await record(db, action="workforce.delegation.created", actor_type="user", actor_id=delegated_by_user_id,
                 tenant_id=tenant_id, resource_type="workforce_delegation", resource_id=delegation.id,
                 metadata={"manager_agent_instance_id": str(manager_agent_instance_id),
                           "allowed_operations": delegation.allowed_operations, "risk_tier": risk_tier,
                           "starts_at": starts_at.isoformat(), "expires_at": expires_at.isoformat()})
    return delegation


async def revoke_delegation(
    db: AsyncSession, *, tenant_id: UUID, delegation_id: UUID, revoked_by_user_id: UUID, reason: str
) -> WorkforceDelegation:
    delegation = (await db.execute(
        select(WorkforceDelegation).where(
            WorkforceDelegation.id == delegation_id,
            WorkforceDelegation.tenant_id == tenant_id,
        ).with_for_update()
    )).scalar_one_or_none()
    if delegation is None:
        raise NotFoundError("Workforce delegation not found")
    if delegation.status == "revoked":
        raise ConflictError("Workforce delegation is already revoked")
    delegation.status = "revoked"
    delegation.revoked_at = datetime.now(timezone.utc)
    delegation.revoked_by_user_id = revoked_by_user_id
    await db.flush()
    await record(db, action="workforce.delegation.revoked", actor_type="user", actor_id=revoked_by_user_id,
                 tenant_id=tenant_id, resource_type="workforce_delegation", resource_id=delegation.id,
                 metadata={"reason": reason})
    return delegation


async def assert_operation_delegated(
    db: AsyncSession, *, tenant_id: UUID, manager_agent_instance_id: UUID,
    operation: str, employee_id: UUID | None = None
) -> WorkforceDelegation:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WorkforceDelegation).where(
            WorkforceDelegation.tenant_id == tenant_id,
            WorkforceDelegation.manager_agent_instance_id == manager_agent_instance_id,
            WorkforceDelegation.status.in_(("active", "scheduled")),
            WorkforceDelegation.starts_at <= now,
            WorkforceDelegation.expires_at > now,
        ).order_by(WorkforceDelegation.expires_at.desc())
    )
    for delegation in result.scalars().all():
        if operation not in set(delegation.allowed_operations):
            continue
        if employee_id is not None and delegation.affected_employee_ids:
            if str(employee_id) not in {str(item) for item in delegation.affected_employee_ids}:
                continue
        return delegation
    raise ValidationAppError("No active CEO delegation authorizes this manager operation")
