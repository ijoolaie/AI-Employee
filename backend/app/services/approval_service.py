"""Human and delegated-agent approval lifecycle for gated executions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.run import Run
from app.models.tool_approval import ToolApprovalRequest
from app.services import audit_service


def validate_resume_approval(
    approval: ToolApprovalRequest,
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    tool_name: str,
    tool_call_id: str,
) -> None:
    """Fail closed unless an approval is current for this exact execution."""
    if approval.tenant_id != tenant_id or approval.run_id != run_id:
        raise ValidationAppError("Approval context does not match the Run tenant")
    if approval.status != "approved":
        raise ValidationAppError("Approval is not currently granted")
    if approval.tool_name != tool_name or approval.tool_call_id != tool_call_id:
        raise ValidationAppError("Approval does not match the requested tool call")


async def create_request(db: AsyncSession, *, tenant_id: uuid.UUID, run: Run, tool_name: str, tool_call_id: str, arguments: dict, continuation_messages: list[dict], iteration: int, requested_by: uuid.UUID | None) -> ToolApprovalRequest:
    existing = await db.execute(select(ToolApprovalRequest).where(ToolApprovalRequest.run_id == run.id, ToolApprovalRequest.tool_call_id == tool_call_id, ToolApprovalRequest.status == "pending"))
    existing_request = existing.scalar_one_or_none()
    if existing_request is not None:
        return existing_request
    approval = ToolApprovalRequest(tenant_id=tenant_id, run_id=run.id, tool_name=tool_name, tool_call_id=tool_call_id, arguments=arguments, continuation_messages=continuation_messages, iteration=iteration, requested_by=requested_by, status="pending")
    db.add(approval)
    run.status = "waiting"
    await db.flush()
    await audit_service.record(db, action="tool.approval_requested", actor_type="system", tenant_id=tenant_id, resource_type="run", resource_id=run.id, request_id=run.request_id, metadata={"approval_id": str(approval.id), "tool": tool_name, "tool_call_id": tool_call_id})
    return approval


async def list_requests(db: AsyncSession, *, tenant_id: uuid.UUID, status: str | None = None):
    stmt = select(ToolApprovalRequest).where(ToolApprovalRequest.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(ToolApprovalRequest.status == status)
    result = await db.execute(stmt.order_by(ToolApprovalRequest.created_at.desc()))
    return list(result.scalars().all())


async def _authorize_agent_decision(db: AsyncSession, *, agent_id: uuid.UUID, tenant_id: uuid.UUID, approval: ToolApprovalRequest) -> AgentInstance:
    result = await db.execute(select(AgentInstance).where(AgentInstance.id == agent_id, AgentInstance.tenant_id == tenant_id).with_for_update())
    agent = result.scalar_one_or_none()
    if agent is None:
        raise NotFoundError("Approval agent not found")
    if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
        raise ConflictError("Approval agent is not available")
    policy = agent.configuration.get("approval_delegation", {}) if isinstance(agent.configuration, dict) else {}
    if policy.get("enabled") is not True:
        raise ConflictError("Agent is not authorized to decide approvals")
    allowed_tools = policy.get("tools")
    if allowed_tools is not None and approval.tool_name not in allowed_tools:
        raise ConflictError("Agent is not authorized for this approval tool")
    allowed_decisions = policy.get("decisions", ["approve", "reject"])
    if not isinstance(allowed_decisions, list):
        raise ConflictError("Invalid agent approval policy")
    return agent


async def decide(db: AsyncSession, *, approval_id: uuid.UUID, tenant_id: uuid.UUID, decided_by: uuid.UUID, decision: str, reason: str | None, actor_type: str = "user") -> ToolApprovalRequest:
    if decision not in {"approve", "reject"}:
        raise ConflictError("unsupported approval decision")
    result = await db.execute(select(ToolApprovalRequest).where(ToolApprovalRequest.id == approval_id, ToolApprovalRequest.tenant_id == tenant_id).with_for_update())
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError("Approval request not found")
    if approval.status != "pending":
        raise ConflictError(f"Approval request already decided: {approval.status}")
    if actor_type == "agent":
        agent = await _authorize_agent_decision(db, agent_id=decided_by, tenant_id=tenant_id, approval=approval)
        policy = agent.configuration.get("approval_delegation", {})
        if decision not in policy.get("decisions", ["approve", "reject"]):
            raise ConflictError("Agent is not authorized for this approval decision")
    elif actor_type != "user":
        raise ConflictError("unsupported approval actor")
    run_result = await db.execute(select(Run).where(Run.id == approval.run_id, Run.tenant_id == tenant_id).with_for_update())
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Run not found for approval")
    approval.status = "approved" if decision == "approve" else "rejected"
    approval.decided_by = decided_by
    approval.decision_reason = reason
    approval.decided_at = datetime.now(timezone.utc)
    run.status = "pending" if approval.status == "approved" else "failed"
    if approval.status == "rejected":
        run.error = {"code": "TOOL_APPROVAL_REJECTED", "message": reason or "Approval rejected."}
    await db.flush()
    await audit_service.record(db, action="tool.approval_decided", actor_type=actor_type, actor_id=decided_by, tenant_id=tenant_id, resource_type="run", resource_id=run.id, request_id=run.request_id, metadata={"approval_id": str(approval.id), "tool": approval.tool_name, "decision": approval.status, "reason": reason})
    return approval
