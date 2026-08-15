from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.core.deps import AuditReadContext, DbSession, WorkflowReadContext, WorkflowExecuteContext
from app.schemas.common import APIResponse
from app.schemas.audit import AuditLogResponse
from app.models.outbox import OutboxMessage
from app.services import audit_service, outbox_service, phase1_observability_service
from app.services.workflow_service import get_workflow_run

router = APIRouter(prefix="/operations", tags=["operations"])

@router.get("/metrics", response_model=APIResponse[dict])
async def get_metrics(ctx: WorkflowReadContext, db: DbSession):
    return APIResponse(success=True, data=await phase1_observability_service.metrics_snapshot(db, tenant_id=ctx.tenant_id))

@router.get("/dead-letters", response_model=APIResponse[list[dict]])
async def list_dead_letters(ctx: WorkflowReadContext, db: DbSession, limit: int = 100):
    rows = await phase1_observability_service.list_dead_letters(db, tenant_id=ctx.tenant_id, limit=limit)
    data=[{"id":str(r.id),"kind":r.kind,"attempts":r.attempts,"last_error":r.last_error,"dead_at":r.dead_at,"replayed_at":r.replayed_at,"payload":r.payload} for r in rows]
    return APIResponse(success=True, data=data)

@router.post("/dead-letters/{message_id}/replay", response_model=APIResponse[dict])
async def replay_dead_letter(message_id: UUID, ctx: WorkflowExecuteContext, db: DbSession):
    row = await db.get(OutboxMessage, message_id)
    if row is None or row.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Dead-letter message not found")
    if row.status != "dead":
        raise HTTPException(status_code=409, detail="Message is not dead-lettered")
    await outbox_service.replay(db, row)
    await db.commit()
    return APIResponse(success=True, data={"id":str(row.id),"status":row.status,"replayed_at":row.replayed_at})


@router.get("/audit-logs", response_model=APIResponse[list[AuditLogResponse]])
async def list_audit_logs(
    ctx: AuditReadContext,
    db: DbSession,
    limit: int = 100,
    action: str | None = None,
    status_filter: str | None = None,
):
    rows = await audit_service.list_logs(
        db,
        tenant_id=ctx.tenant_id,
        limit=limit,
        action=action,
        status=status_filter,
    )
    data = [
        AuditLogResponse(
            id=row.id,
            actor_type=row.actor_type,
            actor_id=row.actor_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            request_id=row.request_id,
            status=row.status,
            metadata=row.metadata_,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return APIResponse(success=True, data=data)
