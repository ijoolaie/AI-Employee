"""Test Center evidence and artifact endpoints (P12.4)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RunExecuteContext, RunReadContext
from app.services.audit_service import record
from app.services.test_center import TestCenterError, TestCenterService

router = APIRouter(prefix="/test-center", tags=["test-center-evidence"])


class EvidenceIdentityUpdate(BaseModel):
    runtime_version: str | None = Field(default=None, max_length=120)
    migration_identity: str | None = Field(default=None, max_length=120)
    git_sha: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[0-9a-fA-F]+$")
    evidence_boundary: str = Field(default="engineering_product_evidence", max_length=80)


class ArtifactCreate(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=255)
    reference: str = Field(min_length=1, max_length=2048)
    sha256: str | None = Field(default=None, min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    metadata: dict = Field(default_factory=dict)


class ArtifactSummary(BaseModel):
    id: UUID
    test_run_id: UUID
    artifact_type: str
    label: str
    reference: str
    sha256: str | None
    size_bytes: int | None
    metadata: dict
    created_at: datetime


def _error(exc: TestCenterError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.post("/runs/{run_id}/evidence-identity")
async def update_evidence_identity(
    run_id: UUID,
    payload: EvidenceIdentityUpdate,
    ctx: RunExecuteContext,
    db: AsyncSession = Depends(get_db),
):
    service = TestCenterService(db)
    try:
        run = await service.record_evidence_identity(
            run_id=run_id,
            tenant_id=ctx.tenant_id,
            **payload.model_dump(),
        )
        await record(
            db,
            action="test_run.evidence_identity.recorded",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            metadata={
                "correlation_id": str(run.correlation_id),
                "runtime_version": run.runtime_version,
                "migration_identity": run.migration_identity,
                "git_sha": run.git_sha,
                "evidence_boundary": run.evidence_boundary,
            },
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return {
        "run_id": run.id,
        "runtime_version": run.runtime_version,
        "migration_identity": run.migration_identity,
        "git_sha": run.git_sha,
        "evidence_boundary": run.evidence_boundary,
    }


@router.post("/runs/{run_id}/artifacts", response_model=ArtifactSummary, status_code=status.HTTP_201_CREATED)
async def add_artifact(
    run_id: UUID,
    payload: ArtifactCreate,
    ctx: RunExecuteContext,
    db: AsyncSession = Depends(get_db),
):
    service = TestCenterService(db)
    try:
        artifact = await service.add_artifact(
            run_id=run_id,
            tenant_id=ctx.tenant_id,
            **payload.model_dump(),
        )
        await record(
            db,
            action="test_run.artifact.added",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run_artifact",
            resource_id=artifact.id,
            metadata={"test_run_id": str(run_id), "artifact_type": artifact.artifact_type},
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return ArtifactSummary.model_validate(artifact, from_attributes=True)


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactSummary])
async def list_artifacts(
    run_id: UUID,
    ctx: RunReadContext,
    db: AsyncSession = Depends(get_db),
):
    service = TestCenterService(db)
    try:
        artifacts = await service.list_artifacts(run_id=run_id, tenant_id=ctx.tenant_id)
    except TestCenterError as exc:
        raise _error(exc) from exc
    return [ArtifactSummary.model_validate(item, from_attributes=True) for item in artifacts]
