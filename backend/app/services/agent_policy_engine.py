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
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate
from app.models.tool_approval import ToolApprovalRequest
from app.services.agent_delegation_service import validate_delegation
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.services.agent_kill_switch_service import assert_not_killed


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
    delegation_id: UUID | None = None
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

    try:
        await assert_not_killed(
            db,
            tenant_id=request.tenant_id,
            agent_instance_id=instance.id,
        )
    except ValidationAppError:
        return result(PolicyDecision.DENY, "agent_emergency_kill_switch_active")

    if instance.status != AgentInstanceStatus.ENABLED or not instance.enabled:
        return result(PolicyDecision.DENY, "agent_instance_not_executable")

    # Governed Stage 8 instances carry the CEO-approved authority fingerprint
    # in their immutable provisioning configuration. Recompute it at every
    # execution boundary so post-activation drift cannot silently expand or
    # otherwise change execution authority.
    template_id = getattr(instance, "agent_template_id", None)
    if template_id is not None:
        template = (
            await db.execute(
                select(AgentTemplate).where(
                    AgentTemplate.id == template_id,
                    AgentTemplate.tenant_id == request.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if template is None or template.status.value != "published":
            return result(PolicyDecision.DENY, "agent_governance_template_invalid")

        configuration = dict(instance.configuration or {})
        approved_fingerprint = configuration.pop(FINGERPRINT_KEY, None)
        if not approved_fingerprint:
            return result(PolicyDecision.DENY, "agent_governance_fingerprint_missing")

        current_fingerprint = execution_authority_fingerprint(
            tenant_id=request.tenant_id,
            template_id=template.id,
            template_version=template.version,
            agent_definition_id=template.agent_definition_id,
            risk_tier=template.risk_tier,
            capability_contract=template.capability_contract,
            permission_policy=template.permission_policy,
            approval_policy=template.approval_policy,
            install_policy=template.install_policy,
            configuration=configuration,
            max_concurrency=instance.max_concurrency,
            budget_policy=instance.budget_policy,
        )
        if current_fingerprint != approved_fingerprint:
            return result(PolicyDecision.DENY, "agent_governance_fingerprint_mismatch")

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

    access_review = (
        await db.execute(
            select(AgentAccessReview)
            .where(
                AgentAccessReview.agent_identity_id == identity.id,
                AgentAccessReview.tenant_id == request.tenant_id,
            )
            .order_by(AgentAccessReview.reviewed_at.desc(), AgentAccessReview.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if access_review is None:
        identity.active = False
        await db.flush()
        return result(PolicyDecision.DENY, "agent_access_review_missing")
    if access_review.decision != AgentAccessReviewDecision.APPROVED:
        identity.active = False
        await db.flush()
        return result(PolicyDecision.DENY, "agent_access_review_not_approved")
    if access_review.next_review_at is not None and access_review.next_review_at <= now:
        identity.active = False
        await db.flush()
        return result(PolicyDecision.DENY, "agent_access_review_expired")

    if request.delegation_id is not None:
        try:
            await validate_delegation(
                db,
                tenant_id=request.tenant_id,
                delegation_id=request.delegation_id,
                delegate_agent_instance_id=instance.id,
                action=request.action,
                tool_name=request.tool_name,
                now=now,
            )
        except ValidationAppError:
            return result(PolicyDecision.DENY, "delegation_invalid")
    elif request.context.get("delegated_from"):
        return result(PolicyDecision.DENY, "delegation_proof_required")

    if request.action == "tool.execute" and not request.tool_name:
        return result(PolicyDecision.DENY, "tool_name_required")

    policy = instance.permission_policy or {}
    allowed_tools = set(policy.get("allowed_tools") or policy.get("tools") or [])
    permissions = set(policy.get("permissions") or [])

    if request.tool_name is not None and request.tool_name not in allowed_tools and "*" not in allowed_tools:
        return result(PolicyDecision.DENY, "tool_not_authorized", allowed_tools=sorted(allowed_tools))

    if request.required_permission is not None and request.required_permission not in permissions and "*" not in permissions:
        return result(PolicyDecision.DENY, "permission_not_granted", required_permission=request.required_permission)

    if request.requires_approval:
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
            f"Human approval required for Agent action: {decision.reason}",
            details={"action": request.action, "tool": request.tool_name, "policy_version": decision.policy_version, "reason": decision.reason},
        )
    if not decision.allowed:
        raise ValidationAppError(
            f"Agent action denied by policy: {decision.reason}",
            details={"action": request.action, "tool": request.tool_name, "policy_version": decision.policy_version, "reason": decision.reason},
        )
    return (
        await db.execute(
            select(AgentInstance).where(
                AgentInstance.id == request.agent_instance_id,
                AgentInstance.tenant_id == request.tenant_id,
            )
        )
    ).scalar_one()
