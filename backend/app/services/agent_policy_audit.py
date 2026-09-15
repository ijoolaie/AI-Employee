"""Audit bridge for governed Agent policy decisions."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import audit_service


async def record_policy_decision_audit(db: AsyncSession, decision) -> None:
    """Persist policy decisions without changing authorization behavior."""
    try:
        await audit_service.record(
            db,
            action="agent.policy.decision",
            actor_type="agent",
            actor_id=str(decision.agent_instance_id),
            tenant_id=decision.tenant_id,
            resource_type=decision.resource_type or "agent_action",
            resource_id=decision.resource_id,
            status=decision.decision.value,
            metadata={
                "policy_version": decision.policy_version,
                "reason": decision.reason,
                "action": decision.action,
                "tool_name": decision.tool_name,
                "required_permission": decision.required_permission,
                **decision.metadata,
            },
        )
    except Exception:
        # Audit failure must not alter authorization behavior.
        return
