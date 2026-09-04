"""Unified V1.5 workspace read model for Human + Agent operations."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.core.deps import AuditReadContext, DbSession
from app.models.tool_approval import ToolApprovalRequest
from app.models.workflow_approval import WorkflowApproval
from app.models.work_item import WorkItem, WorkItemStatus
from app.schemas.common import APIResponse

router = APIRouter(prefix="/workspace", tags=["workspace"])


class WorkspaceWorkItem:
    def __init__(self, item: WorkItem):
        self.id = item.id
        self.title = item.title
        self.status = item.status.value
        self.priority = item.priority
        self.executor_type = item.executor_type.value if item.executor_type else None
        self.executor_id = item.executor_id
        self.requester_id = item.requester_id
        self.created_at = item.created_at
        self.updated_at = item.updated_at


def _approval(approval, kind: str) -> dict:
    return {
        "id": approval.id,
        "kind": kind,
        "status": approval.status,
        "requested_by": approval.requested_by,
        "decided_by": getattr(approval, "decided_by", None),
        "decision_reason": getattr(approval, "decision_reason", None),
        "created_at": approval.created_at,
        "decided_at": getattr(approval, "decided_at", None),
        "metadata": getattr(approval, "metadata_", {}) or {},
    }


@router.get("", response_model=APIResponse[dict])
async def get_workspace(
    ctx: AuditReadContext,
    db: DbSession,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return one tenant-scoped queue for humans, agents, and approval work.

    This is a read-model endpoint only: assignment and approval decisions continue
    through their existing permissioned APIs, preserving the current execution
    and governance boundaries.
    """
    stmt = (
        select(WorkItem)
        .where(WorkItem.tenant_id == ctx.tenant_id)
        .order_by(WorkItem.priority.desc(), WorkItem.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        try:
            parsed_status = WorkItemStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid work item status") from exc
        stmt = stmt.where(WorkItem.status == parsed_status)
    work_items = (await db.execute(stmt)).scalars().all()

    workflow_result = await db.execute(
        select(WorkflowApproval)
        .where(WorkflowApproval.tenant_id == ctx.tenant_id, WorkflowApproval.status == "pending")
        .order_by(WorkflowApproval.created_at.asc())
        .limit(limit)
    )
    tool_result = await db.execute(
        select(ToolApprovalRequest)
        .where(ToolApprovalRequest.tenant_id == ctx.tenant_id, ToolApprovalRequest.status == "pending")
        .order_by(ToolApprovalRequest.created_at.asc())
        .limit(limit)
    )

    items = [WorkspaceWorkItem(item).__dict__ for item in work_items]
    approvals = [_approval(x, "workflow") for x in workflow_result.scalars().all()]
    approvals.extend(_approval(x, "tool") for x in tool_result.scalars().all())
    approvals.sort(key=lambda value: value["created_at"])

    return APIResponse(
        success=True,
        data={
            "work_items": items,
            "pending_approvals": approvals,
            "counts": {
                "work_items": len(items),
                "pending_approvals": len(approvals),
                "human_assigned": sum(1 for item in items if item["executor_type"] == "human"),
                "agent_assigned": sum(1 for item in items if item["executor_type"] == "agent"),
            },
        },
    )
