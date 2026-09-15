"""Governed AgentIdentity lifecycle transitions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.agent_identity import AgentIdentityLifecycleAction
from app.services import audit_service


async def apply_identity_lifecycle(
    db: AsyncSession,
    identity,
    action: AgentIdentityLifecycleAction,
    actor_id=None,
    reason: str | None = None,
) -> None:
    """Apply a controlled identity lifecycle transition and emit audit evidence."""
    now = datetime.now(timezone.utc)

    if action == AgentIdentityLifecycleAction.ACTIVATE:
        identity.active = True
        identity.revoked_at = None
    elif action == AgentIdentityLifecycleAction.SUSPEND:
        identity.active = False
    elif action == AgentIdentityLifecycleAction.REVOKE:
        identity.active = False
        identity.revoked_at = now
    elif action in (
        AgentIdentityLifecycleAction.CREATE,
        AgentIdentityLifecycleAction.ROTATE,
    ):
        identity.active = True

    await audit_service.record(
        db,
        action="agent.identity.lifecycle",
        actor_type="agent",
        actor_id=str(actor_id or identity.agent_instance_id),
        tenant_id=identity.tenant_id,
        resource_type="agent_identity",
        resource_id=identity.id,
        status=action.value,
        metadata={
            "identity_id": str(identity.id),
            "agent_instance_id": str(identity.agent_instance_id),
            "reason": reason,
        },
    )
