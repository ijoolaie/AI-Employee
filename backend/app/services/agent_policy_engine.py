"""Central fail-closed policy decision kernel for governed Agent actions."""
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
from app.models.tool_approval import ToolApprovalRequest


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
    run_id: UUID | None = None
    tool_call_id: str | None = None
    approval_request_id: UUID | None = None
    arguments: dict[str, Any] | None = None
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
    """Evaluate one Agent action deterministically and fail closed."""
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

    if request.action == "tool.execute" and not request.tool_name:
        return result(PolicyDecision.DENY, "tool_name_required")

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

    if request.requires_approval:
        # Approval is an authorization artifact, not caller-controlled state.
        # Bind it to tenant + run + tool + tool-call + exact arguments.
        if not request.run_id or not request.tool_call_id or not request.approval_request_id:
            return result(PolicyDecision.REQUIRE_APPROVAL, "approval_context_required")
        approval = (
            await db.execute(
                select(ToolApprovalRequest).where(
                    ToolApprovalRequest.id == request.approval_request_id,
                    ToolApprovalRequest.tenant_id == request.tenant_id,
                    ToolApprovalRequest.run_id == request.run_id,
                    ToolApprovalRequest.tool_name == request.tool_name,
                    ToolApprovalRequest.status == "approved",
                )
            )
        ).scalar_one_or_none()
        if approval is None:
            return result(PolicyDecision.REQUIRE_APPROVAL, "approval_not_found_or_not_approved")
        if str(getattr(approval, "tool_call_id", "")) != str(request.tool_call_id):
            return result(PolicyDecision.DENY, "approval_tool_call_mismatch")
        if request.arguments is not None and approval.arguments != request.arguments:
            return result(PolicyDecision.DENY, "approval_arguments_mismatch")
        return result(PolicyDecision.ALLOW, "policy_allow_approved")

    if request.approval_granted or request.approval_request_id or request.tool_call_id:
        return result(PolicyDecision.DENY, "unexpected_approval_context")

    return result(PolicyDecision.ALLOW, "policy_allow")


async def assert_authorized(db: AsyncSession, request: PolicyRequest) -> AgentInstance:
    """Raise the canonical application error unless the policy allows."""
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
