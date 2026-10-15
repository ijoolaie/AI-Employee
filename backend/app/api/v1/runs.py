"""Run endpoints (11_Employee_Framework §5). Creating a Run enqueues async
execution through the transactional outbox, so the Run and its execution signal
are committed atomically and can be dispatched once the transaction is visible."""

from uuid import UUID

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.core.deps import DbSession, RunExecuteContext, RunReadContext
from app.models.employee import Employee
from app.models.run import Run
from app.schemas.common import APIResponse
from app.schemas.run import RunCreate, RunResponse
from app.schemas.trace import RunTraceResponse
from app.services import outbox_service, run_read_service, run_service, trace_service

router = APIRouter(prefix="/runs", tags=["runs"])


async def _employee_labels(
    db, employee_ids: list[UUID]
) -> dict[UUID, tuple[str, str]]:
    if not employee_ids:
        return {}
    result = await db.execute(select(Employee).where(Employee.id.in_(employee_ids)))
    return {e.id: (e.name, e.slug) for e in result.scalars().all()}


def _to_response(run: Run, labels: dict[UUID, tuple[str, str]]) -> RunResponse:
    """Build a stable JSON-safe wire representation for a persisted Run.

    PostgreSQL Numeric/JSON values can contain Decimal, UUID, datetime, Enum,
    or other values that are valid Python objects but are not uniformly
    serializable across the SQLAlchemy/Pydantic/FastAPI versions used by the
    production-like certification stack. Normalize the persisted JSON fields
    with FastAPI's canonical encoder before constructing the response model.
    """
    name, slug = labels.get(run.employee_id, (None, None))
    return RunResponse(
        id=run.id,
        employee_id=run.employee_id,
        employee_version_id=run.employee_version_id,
        employee_name=name,
        employee_slug=slug,
        status=str(run.status),
        input_data=jsonable_encoder(run.input_data or {}),
        output_data=jsonable_encoder(run.output_data),
        error=jsonable_encoder(run.error),
        total_tokens=int(run.total_tokens or 0),
        total_cost_usd=float(run.total_cost_usd or 0),
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


@router.post("", response_model=APIResponse[RunResponse], status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreate, ctx: RunExecuteContext, db: DbSession):
    run = await run_service.create_run(
        db,
        tenant_id=ctx.tenant_id,
        employee_id=payload.employee_id,
        input_data=payload.input_data,
        created_by=ctx.user_id,
    )

    # Keep the execution signal in the same transaction as the Run. The
    # dispatcher cannot publish it until this transaction commits, avoiding
    # a worker racing the uncommitted Run row.
    await outbox_service.enqueue(
        db,
        kind="agent.run.execute",
        tenant_id=ctx.tenant_id,
        payload={
            "run_id": str(run.id),
            "tenant_id": str(ctx.tenant_id),
        },
        dedupe_key=f"agent.run.execute:run:{run.id}",
    )

    labels = await _employee_labels(db, [run.employee_id])
    return APIResponse(success=True, data=_to_response(run, labels))


@router.get("", response_model=APIResponse[list[RunResponse]])
async def list_runs(
    ctx: RunReadContext,
    db: DbSession,
    employee_id: UUID | None = None,
):
    """List runs for the caller's tenant. Optional `employee_id` filters to one employee."""
    runs = await run_read_service.list_runs(
        db, tenant_id=ctx.tenant_id, employee_id=employee_id
    )
    labels = await _employee_labels(db, [r.employee_id for r in runs])
    return APIResponse(
        success=True, data=[_to_response(r, labels) for r in runs]
    )


@router.get("/{run_id}", response_model=APIResponse[RunResponse])
async def get_run(run_id: UUID, ctx: RunReadContext, db: DbSession):
    run = await run_read_service.get_run(db, run_id=run_id, tenant_id=ctx.tenant_id)
    labels = await _employee_labels(db, [run.employee_id])
    return APIResponse(success=True, data=_to_response(run, labels))


@router.get("/{run_id}/trace", response_model=APIResponse[RunTraceResponse])
async def get_run_trace(run_id: UUID, ctx: RunReadContext, db: DbSession):
    """Return the durable execution timeline for one tenant-scoped Run."""
    trace = await trace_service.get_run_trace(
        db, run_id=run_id, tenant_id=ctx.tenant_id
    )
    return APIResponse(success=True, data=RunTraceResponse.model_validate(trace))
