"""Human approval endpoints for gated Tool calls."""

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import ApprovalDecideContext, ApprovalReadContext, DbSession
from app.schemas.approval import ApprovalDecision, ToolApprovalResponse
from app.schemas.common import APIResponse
from app.services import approval_service, outbox_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=APIResponse[list[ToolApprovalResponse]])
async def list_approvals(ctx: ApprovalReadContext, db: DbSession, status: str | None = None):
    approvals = await approval_service.list_requests(db, tenant_id=ctx.tenant_id, status=status)
    return APIResponse(success=True, data=[ToolApprovalResponse.model_validate(a) for a in approvals])


@router.post("/{approval_id}/decision", response_model=APIResponse[ToolApprovalResponse])
async def decide_approval(approval_id: UUID, payload: ApprovalDecision, ctx: ApprovalDecideContext, db: DbSession):
    approval = await approval_service.decide(
        db,
        approval_id=approval_id,
        tenant_id=ctx.tenant_id,
        decided_by=ctx.user_id,
        decision=payload.decision,
        reason=payload.reason,
    )
    if approval.status == "approved":
        # The approval decision and its resume signal must become visible as
        # one transaction. Direct Celery enqueue here races the endpoint's
        # dependency-managed commit: a fast worker can consume the task while
        # the approval is still pending, observe Run.status=waiting, and exit
        # without scheduling another execution. Persist the resume through the
        # transactional outbox so it cannot be claimed before this transaction
        # commits, and deterministic dedupe makes retries harmless.
        await outbox_service.enqueue(
            db,
            kind="agent.run.execute",
            tenant_id=ctx.tenant_id,
            payload={
                "run_id": str(approval.run_id),
                "tenant_id": str(ctx.tenant_id),
            },
            dedupe_key=f"agent.run.execute:approval:{approval.id}",
        )
    return APIResponse(success=True, data=ToolApprovalResponse.model_validate(approval))
