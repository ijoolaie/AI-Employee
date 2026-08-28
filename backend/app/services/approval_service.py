"""Human and delegated-agent approval lifecycle for gated executions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.run import Run
from app.models.tool_approval import ToolApprovalRequest
from app.services import audit_service


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


async def decide(db: AsyncSession, *, approval_id: uuid.UUID, tenant_id: uuid.UUID, decided_by: uuid.UUID, decision: str, reason: str | None, actor_type: str = "user") -> ToolApprovalRequest:
    if decision not in {"approve", "reject"}:
        raise ConflictError("unsupported approval decision")
    result = await db.execute(select(ToolApprovalRequest).where(ToolApprovalRequest.id == approval_id, ToolApprovalRequest.tenant_id == tenant_id).with_for_update())
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError("Approval request not found")
    if approval.status != "pending":
        raise ConflictError(f"Approval request already decided: {approval.status}")
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
