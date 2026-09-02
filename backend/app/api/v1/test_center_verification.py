"""Exportable Test Center verification record endpoint (P12.6)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RunReadContext
from app.services.audit_service import record
from app.services.test_center_verification import (
    TestCenterVerificationService,
    VerificationRecordError,
)

router = APIRouter(prefix="/test-center", tags=["test-center-verification"])


@router.get("/runs/{run_id}/verification-record")
async def export_verification_record(
    run_id: UUID,
    ctx: RunReadContext,
    db: AsyncSession = Depends(get_db),
):
    """Export a tenant-scoped verification snapshot without changing the run."""
    service = TestCenterVerificationService(db)
    try:
        record_payload = await service.build_record(tenant_id=ctx.tenant_id, run_id=run_id)
        await record(
            db,
            action="test_run.verification_record.exported",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run_id,
            metadata={
                "correlation_id": str(record_payload["run"]["correlation_id"]),
                "evidence_boundary": record_payload["acceptance_boundary"],
                "schema_version": record_payload["schema_version"],
            },
        )
        await db.commit()
    except VerificationRecordError as exc:
        await db.rollback()
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=message) from exc

    return JSONResponse(
        content=jsonable_encoder(record_payload),
        headers={
            "Content-Disposition": f'attachment; filename="test-run-{run_id}-verification.json"',
            "X-Evidence-Boundary": "engineering_product_evidence",
        },
    )
