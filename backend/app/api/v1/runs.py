"""Run endpoints (11_Employee_Framework §5). Creating a Run enqueues async
execution on Celery; if the broker is unreachable (e.g. local dev without
`docker compose up`), the Run is still created as 'pending' so nothing is
lost — it can be retried via the worker once the queue is back."""

import logging
from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select

from app.core.deps import DbSession, RunExecuteContext, RunReadContext
from app.models.employee import Employee
from app.models.run import Run
from app.schemas.common import APIResponse
from app.schemas.run import RunCreate, RunResponse
from app.schemas.trace import RunTraceResponse
from app.services import run_service, trace_service

logger = logging.getLogger("app.api.runs")
router = APIRouter(prefix="/runs", tags=["runs"])


async def _employee_labels(
    db, employee_ids: list[UUID]
) -> dict[UUID, tuple[str, str]]:
    if not employee_ids:
        return {}
    result = await db.execute(select(Employee).where(Employee.id.in_(employee_ids)))
    return {e.id: (e.name, e.slug) for e in result.scalars().all()}


def _to_response(run: Run, labels: dict[UUID, tuple[str, str]]) -> RunResponse:
    name, slug = labels.get(run.employee_id, (None, None))
    data = RunResponse.model_validate(run)
    return data.model_copy(update={"employee_name": name, "employee_slug": slug})


@router.post("", response_model=APIResponse[RunResponse], status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreate, ctx: RunExecuteContext, db: DbSession):
    run = await run_service.create_run(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=payload.employee_id,
        input_data=payload.input_data,
        created_by=ctx.user_id,
    )

    try:
        from app.workers.run_worker import execute_run_task

        execute_run_task.delay(str(run.id), str(ctx.tenant_id))
    except Exception:  # noqa: BLE001
        logger.warning("run_enqueue_failed", extra={"run_id": str(run.id)}, exc_info=True)

    labels = await _employee_labels(db, [run.employee_id])
    return APIResponse(success=True, data=_to_response(run, labels))


@router.get("", response_model=APIResponse[list[RunResponse]])
async def list_runs(
    ctx: RunReadContext,
    db: DbSession,
    employee_id: UUID | None = None,
):
    """List runs for the caller's tenant. Optional `employee_id` filters to one employee."""
    runs = await run_service.list_runs(
        db, tenant_id=ctx.tenant_id, employee_id=employee_id
    )
    labels = await _employee_labels(db, [r.employee_id for r in runs])
    return APIResponse(
        success=True, data=[_to_response(r, labels) for r in runs]
    )


@router.get("/{run_id}", response_model=APIResponse[RunResponse])
async def get_run(run_id: UUID, ctx: RunReadContext, db: DbSession):
    run = await run_service.get_run(db, run_id=run_id, tenant_id=ctx.tenant_id)
    labels = await _employee_labels(db, [run.employee_id])
    return APIResponse(success=True, data=_to_response(run, labels))


@router.get("/{run_id}/trace", response_model=APIResponse[RunTraceResponse])
async def get_run_trace(run_id: UUID, ctx: RunReadContext, db: DbSession):
    """Return the durable execution timeline for one tenant-scoped Run."""
    trace = await trace_service.get_run_trace(
        db, run_id=run_id, tenant_id=ctx.tenant_id
    )
    return APIResponse(success=True, data=RunTraceResponse.model_validate(trace))
