"""Run endpoints (11_Employee_Framework §5). Creating a Run enqueues async
execution through the transactional outbox, so the Run and its execution signal
are committed atomically and can be dispatched once the transaction is visible."""

import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.core.deps import DbSession, RunExecuteContext, RunReadContext
from app.models.employee import Employee
from app.models.run import Run
from app.models.audit_log import AuditLog
from app.schemas.common import APIResponse
from app.schemas.run import RunCreate, RunResponse
from app.schemas.trace import RunTraceResponse
from app.services import outbox_service, run_read_service, run_service, trace_service, storage

router = APIRouter(prefix="/runs", tags=["runs"])


class RunArtifactSummary(BaseModel):
    """Safe client contract for one persisted workforce artifact associated with a Run."""

    artifact_id: str
    kind: str
    operation: str | None = None
    status: str | None = None
    created_at: str
    tool: str
    content_type: str
    size_bytes: int
    download_url: str
    provenance: dict[str, Any]


async def _run_artifacts(db, *, run_id: UUID, tenant_id: UUID) -> list[dict[str, Any]]:
    # Check Run ownership before resolving any artifact references.
    await run_read_service.get_run(db, run_id=run_id, tenant_id=tenant_id)
    rows = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action == "tool.call",
            AuditLog.resource_type == "run",
            AuditLog.resource_id == str(run_id),
        )
        .order_by(AuditLog.created_at.asc())
    )
    backend = storage.get_storage_backend()
    artifacts: dict[str, dict[str, Any]] = {}
    for audit in rows.scalars().all():
        metadata = audit.metadata_ if isinstance(audit.metadata_, dict) else {}
        ref = metadata.get("persisted_workforce_artifact")
        if not isinstance(ref, dict):
            continue
        artifact_id = ref.get("artifact_id")
        key = ref.get("storage_key")
        tool = ref.get("tool")
        if (
            not isinstance(artifact_id, str)
            or not artifact_id
            or not isinstance(key, str)
            or not key.startswith(f"{tenant_id}/")
            or not isinstance(tool, str)
            or not tool.startswith("workforce_")
            or not backend.exists(key)
        ):
            continue
        try:
            with backend.open(key) as stream:
                raw = stream.read()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        payload_id = payload.get("artifact_id")
        # If the tool returned an embedded artifact ID, bind it to the audit pointer.
        expected_payload_id = ref.get("payload_artifact_id")
        if isinstance(expected_payload_id, str) and payload_id != expected_payload_id:
            continue
        provenance = {
            key_name: payload[key_name]
            for key_name in ("provider_execution", "external_side_effect", "approval_required", "version")
            if key_name in payload and isinstance(payload[key_name], (str, bool, int, float, type(None)))
        }
        created_at = payload.get("created_at")
        if not isinstance(created_at, str):
            created_at = audit.created_at.isoformat() if audit.created_at else datetime.now(timezone.utc).isoformat()
        item = {
            "artifact_id": artifact_id,
            "kind": str(payload.get("kind") or "workforce_artifact"),
            "operation": payload.get("operation") if isinstance(payload.get("operation"), str) else None,
            "status": payload.get("status") if isinstance(payload.get("status"), str) else None,
            "created_at": created_at,
            "tool": tool,
            "content_type": "application/json",
            "size_bytes": len(raw),
            "download_url": f"/runs/{run_id}/artifacts/{artifact_id}/download",
            "provenance": provenance,
            "_storage_key": key,
        }
        artifacts[artifact_id] = item
    return list(artifacts.values())


@router.get("/{run_id}/artifacts", response_model=APIResponse[list[RunArtifactSummary]])
async def list_run_artifacts(run_id: UUID, ctx: RunReadContext, db: DbSession):
    """List persisted workforce artifacts only through trusted Run audit references."""
    artifacts = await _run_artifacts(db, run_id=run_id, tenant_id=ctx.tenant_id)
    public_items = [{key: value for key, value in item.items() if key != "_storage_key"} for item in artifacts]
    return APIResponse(success=True, data=[RunArtifactSummary.model_validate(item) for item in public_items])


@router.get("/{run_id}/artifacts/{artifact_id}/download")
async def download_run_artifact(run_id: UUID, artifact_id: str, ctx: RunReadContext, db: DbSession):
    """Download JSON only after resolving an artifact through this tenant's exact Run audit records."""
    artifacts = await _run_artifacts(db, run_id=run_id, tenant_id=ctx.tenant_id)
    item = next((candidate for candidate in artifacts if candidate["artifact_id"] == artifact_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Run artifact not found")
    backend = storage.get_storage_backend()
    key = item["_storage_key"]
    if not key.startswith(f"{ctx.tenant_id}/") or not backend.exists(key):
        raise HTTPException(status_code=404, detail="Run artifact not found")
    with backend.open(key) as stream:
        content = stream.read()
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="workforce-artifact-{artifact_id[:64]}.json"'},
    )



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
