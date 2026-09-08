"""Central policy decision kernel for governed Agent actions.

The policy engine is deliberately fail-closed and returns an explicit decision
instead of scattering authorization rules across execution adapters. It is the
single semantic place where identity, lifecycle, tool and permission checks are
combined. Resource/work-item scope and budget checks can be added as policy
rules without changing callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus


POLICY_VERSION = "agent-policy-v1"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class PolicyRequest:
    tenant_id: UUID
    agent_instance_id: UUID
    action: str
    tool_name: str | None = None
    required_permission: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    work_item_id: UUID | None = None
    approval_granted: bool = False
    requires_approval: bool = False
    now: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    policy_version: str
    reason: str
    agent_instance_id: UUID
    tenant_id: UUID
    action: str
    tool_name: str | None = None
    required_permission: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOW


async def authorize(db: AsyncSession, request: PolicyRequest) -> PolicyResult:
    """Evaluate one Agent action using deterministic fail-closed rules."""
    now = request.now or datetime.now(timezone.utc)
    instance = (
        await db.execute(
            select(AgentInstance).where(
                AgentInstance.id == request.agent_instance_id,
                AgentInstance.tenant_id == request.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found for tenant")

    def result(decision: PolicyDecision, reason: str, **metadata: Any) -> PolicyResult:
        return PolicyResult(
            decision=decision,
            policy_version=POLICY_VERSION,
            reason=reason,
            agent_instance_id=instance.id,
            tenant_id=request.tenant_id,
            action=request.action,
            tool_name=request.tool_name,
            required_permission=request.required_permission,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            metadata=metadata,
        )

    if instance.status != AgentInstanceStatus.ENABLED or not instance.enabled:
        return result(PolicyDecision.DENY, "agent_instance_not_executable")

    identity = (
        await db.execute(
            select(AgentIdentity).where(
                AgentIdentity.agent_instance_id == instance.id,
                AgentIdentity.tenant_id == request.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if identity is None:
        return result(PolicyDecision.DENY, "agent_identity_missing")
    if not identity.active or identity.revoked_at is not None:
        return result(PolicyDecision.DENY, "agent_identity_revoked")
    if identity.expires_at is not None and identity.expires_at <= now:
        identity.active = False
        await db.flush()
        return result(PolicyDecision.DENY, "agent_identity_expired")

    policy = instance.permission_policy or {}
    allowed_tools = set(policy.get("allowed_tools") or policy.get("tools") or [])
    permissions = set(policy.get("permissions") or [])

    if request.tool_name is not None and request.tool_name not in allowed_tools and "*" not in allowed_tools:
        return result(PolicyDecision.DENY, "tool_not_authorized", allowed_tools=sorted(allowed_tools))

    if request.required_permission is not None and request.required_permission not in permissions and "*" not in permissions:
        return result(
            PolicyDecision.DENY,
            "permission_not_granted",
            required_permission=request.required_permission,
        )

    if request.requires_approval and not request.approval_granted:
        return result(PolicyDecision.REQUIRE_APPROVAL, "human_approval_required")

    return result(PolicyDecision.ALLOW, "policy_allow")


async def assert_authorized(db: AsyncSession, request: PolicyRequest) -> AgentInstance:
    """Compatibility guard: raise the canonical application error on deny."""
    decision = await authorize(db, request)
    if decision.decision == PolicyDecision.REQUIRE_APPROVAL:
        raise ValidationAppError(
            "Human approval required for Agent action",
            details={
                "action": request.action,
                "tool": request.tool_name,
                "policy_version": decision.policy_version,
                "reason": decision.reason,
            },
        )
    if not decision.allowed:
        raise ValidationAppError(
            "Agent action denied by policy",
            details={
                "action": request.action,
                "tool": request.tool_name,
                "policy_version": decision.policy_version,
                "reason": decision.reason,
            },
        )
    return (
        await db.execute(
            select(AgentInstance).where(
                AgentInstance.id == request.agent_instance_id,
                AgentInstance.tenant_id == request.tenant_id,
            )
        )
    ).scalar_one()
