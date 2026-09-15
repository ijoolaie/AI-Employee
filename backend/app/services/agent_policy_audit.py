"""Audit helpers for Agent policy decisions.

Keeps policy evidence generation centralized so ALLOW/DENY/approval decisions
can be recorded in the immutable audit ledger without duplicating metadata
construction across execution paths.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import audit_service


async def record_policy_decision(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    agent_instance_id: UUID,
    action: str,
    decision: str,
    reason: str,
    policy_version: str,
    tool_name: str | None = None,
    run_id: UUID | None = None,
    tool_call_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Persist one policy decision as governance evidence."""
    await audit_service.record(
        db,
        action="agent.policy.decision",
        actor_type="agent",
        actor_id=agent_instance_id,
        tenant_id=tenant_id,
        resource_type="agent_action",
        resource_id=action,
        status=decision,
        metadata={
            "reason": reason,
            "policy_version": policy_version,
            "tool_name": tool_name,
            "run_id": str(run_id) if run_id else None,
            "tool_call_id": tool_call_id,
            **(metadata or {}),
        },
    )
