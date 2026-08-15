from uuid import UUID
from fastapi import APIRouter, status, Header
from app.core.deps import DbSession, WorkflowReadContext, WorkflowWriteContext, WorkflowExecuteContext, WorkflowCancelContext
from app.schemas.common import APIResponse
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowRunCreate, WorkflowRunResponse, WorkflowCancelRequest, WorkflowVersionCreate, WorkflowVersionResponse, WorkflowReplayRequest
from app.services import workflow_service, workflow_observability_service
from app.models.workflow import WorkflowVersion, WorkflowRun
from sqlalchemy import select

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=APIResponse[WorkflowResponse], status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowCreate, ctx: WorkflowWriteContext, db: DbSession):
    workflow = await workflow_service.create_workflow(db, tenant_id=ctx.tenant_id, created_by=ctx.user_id, slug=payload.slug, name=payload.name, steps=[s.model_dump(mode="json") for s in payload.steps], trigger_type=payload.trigger_type, max_runtime_seconds=payload.max_runtime_seconds)
    version = await workflow_service.get_current_version(db, workflow_id=workflow.id)
    return APIResponse(success=True, data=WorkflowResponse.model_validate(workflow).model_copy(update={"current_version_id": version.id}))




@router.get("", response_model=APIResponse[list[WorkflowResponse]])
async def list_workflows(ctx: WorkflowReadContext, db: DbSession):
    workflows = await workflow_service.list_workflows(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[WorkflowResponse.model_validate(w) for w in workflows])



@router.get("/{workflow_id}/versions", response_model=APIResponse[list[WorkflowVersionResponse]])
async def list_workflow_versions(workflow_id: UUID, ctx: WorkflowReadContext, db: DbSession):
    workflow = await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow.id).order_by(WorkflowVersion.version_number.desc()))
    versions = list(result.scalars().all())
    return APIResponse(success=True, data=[WorkflowVersionResponse.model_validate(v) for v in versions])


@router.get("/{workflow_id}/versions/{version_id}", response_model=APIResponse[WorkflowVersionResponse])
async def get_workflow_version(workflow_id: UUID, version_id: UUID, ctx: WorkflowReadContext, db: DbSession):
    from fastapi import HTTPException
    await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == workflow_id))
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="Workflow version not found")
    return APIResponse(success=True, data=WorkflowVersionResponse.model_validate(version))


@router.post("/{workflow_id}/versions", response_model=APIResponse[WorkflowVersionResponse], status_code=status.HTTP_201_CREATED)
async def create_workflow_version(workflow_id: UUID, payload: WorkflowVersionCreate, ctx: WorkflowWriteContext, db: DbSession):
    version = await workflow_service.create_workflow_version(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, created_by=ctx.user_id, steps=[s.model_dump(mode="json") for s in payload.steps], trigger_type=payload.trigger_type, max_runtime_seconds=payload.max_runtime_seconds, activate=payload.activate)
    return APIResponse(success=True, data=WorkflowVersionResponse.model_validate(version))


@router.post("/{workflow_id}/versions/{version_id}/activate", response_model=APIResponse[WorkflowVersionResponse])
async def activate_workflow_version(workflow_id: UUID, version_id: UUID, ctx: WorkflowWriteContext, db: DbSession):
    version = await workflow_service.activate_workflow_version(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, version_id=version_id, actor_id=ctx.user_id)
    return APIResponse(success=True, data=WorkflowVersionResponse.model_validate(version))

@router.post("/{workflow_id}/runs", response_model=APIResponse[WorkflowRunResponse], status_code=status.HTTP_201_CREATED)
async def create_workflow_run(workflow_id: UUID, payload: WorkflowRunCreate, ctx: WorkflowExecuteContext, db: DbSession, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = idempotency_key or payload.idempotency_key
    run = await workflow_service.create_workflow_run(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, input_data=payload.input_data, created_by=ctx.user_id, idempotency_key=key, workflow_version_id=payload.workflow_version_id)
    from app.services.outbox_service import enqueue
    await enqueue(db, kind="workflow.execute", tenant_id=ctx.tenant_id, payload={"workflow_run_id": str(run.id)}, dedupe_key=f"workflow.execute:{run.id}:initial")
    return APIResponse(success=True, data=WorkflowRunResponse.model_validate(run))


@router.get("/{workflow_id}/runs", response_model=APIResponse[list[WorkflowRunResponse]])
async def list_workflow_runs(workflow_id: UUID, ctx: WorkflowReadContext, db: DbSession):
    workflow = await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    result = await db.execute(
        select(WorkflowRun)
        .where(
            WorkflowRun.workflow_id == workflow.id,
            WorkflowRun.tenant_id == ctx.tenant_id,
        )
        .order_by(workflow_service.WorkflowRun.created_at.desc())
        .limit(100)
    )
    return APIResponse(success=True, data=[WorkflowRunResponse.model_validate(r) for r in result.scalars().all()])

@router.get("/{workflow_id}/runs/{run_id}", response_model=APIResponse[WorkflowRunResponse])
async def get_workflow_run(workflow_id: UUID, run_id: UUID, ctx: WorkflowReadContext, db: DbSession):
    run = await workflow_service.get_workflow_run(db, workflow_run_id=run_id, tenant_id=ctx.tenant_id)
    if run.workflow_id != workflow_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return APIResponse(success=True, data=WorkflowRunResponse.model_validate(run))

@router.get("/{workflow_id}/runs/{run_id}/observability", response_model=APIResponse[dict])
async def get_workflow_observability(workflow_id: UUID, run_id: UUID, ctx: WorkflowReadContext, db: DbSession):
    run = await workflow_service.get_workflow_run(db, workflow_run_id=run_id, tenant_id=ctx.tenant_id)
    if run.workflow_id != workflow_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow run not found")
    data = await workflow_observability_service.get_workflow_observability(db, workflow_run_id=run_id, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=data)


@router.post("/{workflow_id}/runs/{run_id}/replay", response_model=APIResponse[WorkflowRunResponse], status_code=status.HTTP_201_CREATED)
async def replay_workflow_run(workflow_id: UUID, run_id: UUID, payload: WorkflowReplayRequest, ctx: WorkflowExecuteContext, db: DbSession):
    run = await workflow_service.replay_workflow_run(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, source_run_id=run_id, created_by=ctx.user_id, idempotency_key=payload.idempotency_key)
    from app.services.outbox_service import enqueue
    await enqueue(db, kind="workflow.execute", tenant_id=ctx.tenant_id, payload={"workflow_run_id": str(run.id), "reason": "replay", "generation": 0}, dedupe_key=f"workflow.execute:{run.id}:replay")
    return APIResponse(success=True, data=WorkflowRunResponse.model_validate(run))


@router.post("/{workflow_id}/runs/{run_id}/cancel", response_model=APIResponse[WorkflowRunResponse])
async def cancel_workflow_run(workflow_id: UUID, run_id: UUID, payload: WorkflowCancelRequest, ctx: WorkflowCancelContext, db: DbSession):
    run = await workflow_service.get_workflow_run(db, workflow_run_id=run_id, tenant_id=ctx.tenant_id)
    if run.workflow_id != workflow_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow run not found")
    reason = payload.reason
    run = await workflow_service.cancel_workflow_run(db, workflow_run_id=run_id, tenant_id=ctx.tenant_id, cancelled_by=ctx.user_id, reason=reason)
    return APIResponse(success=True, data=WorkflowRunResponse.model_validate(run))
