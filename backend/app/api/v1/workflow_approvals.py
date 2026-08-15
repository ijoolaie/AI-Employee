"""Human approval API for durable workflow wait/resume."""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, status
from sqlalchemy import select
from app.core.deps import DbSession, WorkflowApprovalReadContext, WorkflowApprovalDecideContext
from app.models.workflow_approval import WorkflowApproval
from app.models.workflow import WorkflowRun, WorkflowStepRun
from app.schemas.common import APIResponse
from app.schemas.workflow import WorkflowApprovalDecision, WorkflowApprovalResponse
from app.services import audit_service

router = APIRouter(prefix="/workflow-approvals", tags=["workflow-approvals"])

@router.get("", response_model=APIResponse[list[WorkflowApprovalResponse]])
async def list_workflow_approvals(ctx: WorkflowApprovalReadContext, db: DbSession, status_filter: str | None = None):
    stmt = select(WorkflowApproval).where(WorkflowApproval.tenant_id == ctx.tenant_id)
    if status_filter: stmt = stmt.where(WorkflowApproval.status == status_filter)
    result = await db.execute(stmt.order_by(WorkflowApproval.created_at.desc()))
    return APIResponse(success=True, data=[WorkflowApprovalResponse.model_validate(x) for x in result.scalars().all()])

@router.post("/{approval_id}/decision", response_model=APIResponse[WorkflowApprovalResponse])
async def decide_workflow_approval(approval_id: UUID, payload: WorkflowApprovalDecision, ctx: WorkflowApprovalDecideContext, db: DbSession):
    result = await db.execute(select(WorkflowApproval).where(WorkflowApproval.id == approval_id, WorkflowApproval.tenant_id == ctx.tenant_id).with_for_update())
    approval = result.scalar_one_or_none()
    if approval is None: from fastapi import HTTPException; raise HTTPException(status_code=404, detail="Workflow approval not found")
    if approval.status != "pending": from fastapi import HTTPException; raise HTTPException(status_code=409, detail=f"Approval already decided: {approval.status}")
    now = datetime.now(timezone.utc)
    if approval.expires_at and approval.expires_at <= now:
        approval.status = "expired"; approval.decided_at = now
        await db.commit()
        from fastapi import HTTPException; raise HTTPException(status_code=409, detail="Workflow approval expired")
    approval.status = "approved" if payload.decision == "approve" else "rejected"
    approval.decided_by = ctx.user_id; approval.decision_reason = payload.reason; approval.decided_at = now
    step_result = await db.execute(select(WorkflowStepRun).where(WorkflowStepRun.id == approval.workflow_step_run_id).with_for_update())
    step = step_result.scalar_one_or_none()
    run_result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == approval.workflow_run_id, WorkflowRun.tenant_id == ctx.tenant_id).with_for_update())
    run = run_result.scalar_one_or_none()
    if step is None or run is None: from fastapi import HTTPException; raise HTTPException(status_code=404, detail="Workflow approval state not found")
    if approval.status == "rejected":
        step.status = "failed"; step.error = {"code":"WORKFLOW_APPROVAL_REJECTED","message":payload.reason or "Human approval rejected the workflow step."}; run.status = "failed"; run.error = step.error
    else:
        step.status = "waiting"; run.status = "pending"
    await audit_service.record(db, action="workflow.approval.decided", actor_type="user", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="workflow_approval", resource_id=approval.id, request_id=None, metadata={"workflow_run_id":str(run.id),"step_key":approval.step_key,"decision":approval.status})
    if approval.status == "approved":
        from app.services.workflow_service import _enqueue_resume
        await _enqueue_resume(db, run, reason=f"approval:{approval.id}")
    await db.commit()
    return APIResponse(success=True, data=WorkflowApprovalResponse.model_validate(approval))
