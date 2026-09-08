"""Fail-closed emergency revocation for Agent execution."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationAppError
from app.models.agent_instance import AgentInstance
from app.models.agent_kill_switch import AgentKillScope, AgentKillSwitch
from app.services import audit_service


async def assert_not_killed(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
) -> None:
    """Reject execution when any active global, tenant, or agent kill switch applies."""
    result = await db.execute(
        select(AgentKillSwitch)
        .where(
            AgentKillSwitch.active.is_(True),
            (
                (AgentKillSwitch.scope == AgentKillScope.GLOBAL)
                | ((AgentKillSwitch.scope == AgentKillScope.TENANT) & (AgentKillSwitch.tenant_id == tenant_id))
                | ((AgentKillSwitch.scope == AgentKillScope.AGENT) & (AgentKillSwitch.tenant_id == tenant_id) & (AgentKillSwitch.agent_instance_id == agent_instance_id))
            ),
        )
        .order_by(AgentKillSwitch.asserted_at.desc())
    )
    switch = result.scalars().first()
    if switch is None:
        return
    raise ValidationAppError(
        "Agent execution revoked by emergency kill switch",
        details={"kill_switch_id": str(switch.id), "scope": switch.scope.value, "reason": switch.reason},
    )


async def assert_kill(
    db: AsyncSession,
    *,
    scope: AgentKillScope,
    reason: str,
    asserted_by: uuid.UUID | None,
    tenant_id: uuid.UUID | None = None,
    agent_instance_id: uuid.UUID | None = None,
    correlation_id: str | None = None,
) -> AgentKillSwitch:
    if not reason.strip():
        raise ValidationAppError("Emergency kill switch requires a reason")
    if scope == AgentKillScope.GLOBAL and (tenant_id is not None or agent_instance_id is not None):
        raise ValidationAppError("Global kill switch cannot target a tenant or Agent")
    if scope == AgentKillScope.TENANT and (tenant_id is None or agent_instance_id is not None):
        raise ValidationAppError("Tenant kill switch requires exactly one tenant")
    if scope == AgentKillScope.AGENT and (tenant_id is None or agent_instance_id is None):
        raise ValidationAppError("Agent kill switch requires tenant and Agent instance")

    if scope == AgentKillScope.AGENT:
        instance = (
            await db.execute(
                select(AgentInstance).where(
                    AgentInstance.id == agent_instance_id,
                    AgentInstance.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if instance is None:
            raise ValidationAppError("Agent kill switch target does not belong to tenant")

    # Serialize assertions for the same logical scope. The partial unique indexes
    # remain the database backstop, while the transaction advisory lock removes the
    # check-then-insert race that otherwise surfaces as an IntegrityError.
    lock_key = f"agent-kill:{scope.value}:{tenant_id or '-'}:{agent_instance_id or '-'}"
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))").bindparams(lock_key=lock_key))

    existing = (await db.execute(
        select(AgentKillSwitch).where(
            AgentKillSwitch.scope == scope,
            AgentKillSwitch.active.is_(True),
            AgentKillSwitch.tenant_id == tenant_id,
            AgentKillSwitch.agent_instance_id == agent_instance_id,
        ).with_for_update()
    )).scalar_one_or_none()
    if existing is not None:
        return existing

    switch = AgentKillSwitch(
        scope=scope,
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
        reason=reason.strip(),
        asserted_by=asserted_by,
        correlation_id=correlation_id or str(uuid.uuid4()),
        active=True,
    )
    db.add(switch)
    await db.flush()
    await audit_service.record(
        db,
        action="agent.kill_switch.asserted",
        actor_type="user" if asserted_by else "system",
        actor_id=asserted_by,
        tenant_id=tenant_id,
        resource_type="agent_kill_switch",
        resource_id=switch.id,
        metadata={"scope": scope.value, "agent_instance_id": str(agent_instance_id) if agent_instance_id else None, "reason": reason.strip()},
    )
    return switch


async def revoke_kill(
    db: AsyncSession,
    *,
    kill_switch_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    tenant_id: uuid.UUID | None,
) -> AgentKillSwitch:
    switch = (await db.execute(
        select(AgentKillSwitch).where(AgentKillSwitch.id == kill_switch_id).with_for_update()
    )).scalar_one_or_none()
    if switch is None:
        raise ConflictError("Kill switch not found")
    if switch.tenant_id is not None and switch.tenant_id != tenant_id:
        raise ValidationAppError("Kill switch tenant mismatch")
    if not switch.active:
        return switch
    switch.active = False
    switch.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(
        db,
        action="agent.kill_switch.revoked",
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        tenant_id=switch.tenant_id,
        resource_type="agent_kill_switch",
        resource_id=switch.id,
        metadata={"scope": switch.scope.value},
    )
    return switch
