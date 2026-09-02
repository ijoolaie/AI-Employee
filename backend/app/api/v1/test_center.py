"""Phase 12 Test Center backend contract: definitions, runs and evidence."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RunExecuteContext, RunReadContext
from app.models.test_definition import TestDefinition
from app.models.test_run import TestRun, TestRunStatus
from app.models.test_run_artifact import TestRunArtifact
from app.services.audit_service import record
from app.services.test_center import TestCenterError, TestCenterService

router = APIRouter(prefix="/test-center", tags=["test-center"])


class TestDefinitionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    name: str = Field(min_length=1, max_length=255)
    test_type: str = Field(default="acceptance", max_length=50)
    category: str = Field(default="backend", max_length=80)
    description: str | None = None
    workspace_key: str | None = Field(default=None, max_length=120)
    prerequisites: dict = Field(default_factory=dict)
    expected_result: dict = Field(default_factory=dict)
    evidence_requirements: dict = Field(default_factory=dict)


class TestDefinitionSummary(BaseModel):
    id: UUID
    code: str
    name: str
    test_type: str
    category: str
    description: str | None
    workspace_key: str | None
    prerequisites: dict
    expected_result: dict
    evidence_requirements: dict
    enabled: bool
    created_at: datetime
    updated_at: datetime


class TestRunCreate(BaseModel):
    test_definition_id: UUID
    workspace_key: str | None = Field(default=None, max_length=120)
    fixtures: dict = Field(default_factory=dict)


class TestRunFinish(BaseModel):
    passed: bool
    result: dict = Field(default_factory=dict)
    evidence: dict = Field(default_factory=dict)
    error: str | None = None
    runtime_version: str | None = Field(default=None, max_length=120)
    migration_identity: str | None = Field(default=None, max_length=120)
    git_sha: str | None = Field(default=None, min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")


class TestRunArtifactCreate(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=255)
    reference: str = Field(min_length=1, max_length=2048)
    sha256: str | None = Field(default=None, min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    metadata: dict = Field(default_factory=dict)


class TestRunArtifactSummary(BaseModel):
    id: UUID
    artifact_type: str
    label: str
    reference: str
    sha256: str | None
    size_bytes: int | None
    metadata: dict
    created_at: datetime


class TestRunSummary(BaseModel):
    id: UUID
    test_definition_id: UUID
    workspace_key: str | None
    status: str
    actor_id: UUID | None
    executor_type: str
    correlation_id: UUID
    fixtures: dict
    result: dict | None
    error: str | None
    evidence: dict
    runtime_version: str | None
    migration_identity: str | None
    git_sha: str | None
    evidence_boundary: str
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


def _definition_summary(item: TestDefinition) -> TestDefinitionSummary:
    return TestDefinitionSummary.model_validate(item, from_attributes=True)


def _run_summary(item: TestRun) -> TestRunSummary:
    return TestRunSummary(
        id=item.id,
        test_definition_id=item.test_definition_id,
        workspace_key=item.workspace_key,
        status=item.status.value,
        actor_id=item.actor_id,
        executor_type=item.executor_type,
        correlation_id=item.correlation_id,
        fixtures=item.fixtures or {},
        result=item.result,
        error=item.error,
        evidence=item.evidence or {},
        runtime_version=item.runtime_version,
        migration_identity=item.migration_identity,
        git_sha=item.git_sha,
        evidence_boundary=item.evidence_boundary,
        queued_at=item.queued_at,
        started_at=item.started_at,
        finished_at=item.finished_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _artifact_summary(item: TestRunArtifact) -> TestRunArtifactSummary:
    return TestRunArtifactSummary(
        id=item.id,
        artifact_type=item.artifact_type,
        label=item.label,
        reference=item.reference,
        sha256=item.sha256,
        size_bytes=item.size_bytes,
        metadata=item.metadata or {},
        created_at=item.created_at,
    )


def _error(exc: TestCenterError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.get("/definitions", response_model=list[TestDefinitionSummary])
async def list_definitions(
    ctx: RunReadContext,
    db: AsyncSession = Depends(get_db),
    workspace_key: str | None = Query(default=None),
):
    stmt = select(TestDefinition).where(TestDefinition.tenant_id == ctx.tenant_id).order_by(TestDefinition.created_at.desc())
    if workspace_key is not None:
        stmt = stmt.where(TestDefinition.workspace_key == workspace_key)
    result = await db.execute(stmt)
    return [_definition_summary(item) for item in result.scalars().all()]


@router.post("/definitions", response_model=TestDefinitionSummary, status_code=status.HTTP_201_CREATED)
async def create_definition(
    payload: TestDefinitionCreate,
    ctx: RunExecuteContext,
    db: AsyncSession = Depends(get_db),
):
    definition = TestDefinition(tenant_id=ctx.tenant_id, created_by=ctx.user_id, **payload.model_dump())
    db.add(definition)
    try:
        await db.flush()
        await record(
            db,
            action="test_definition.created",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_definition",
            resource_id=definition.id,
            metadata={"code": definition.code, "category": definition.category},
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="test definition already exists or is invalid") from exc
    return _definition_summary(definition)


@router.post("/runs", response_model=TestRunSummary, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: TestRunCreate,
    ctx: RunExecuteContext,
    db: AsyncSession = Depends(get_db),
):
    service = TestCenterService(db)
    try:
        run = await service.create_run(tenant_id=ctx.tenant_id, actor_id=ctx.user_id, **payload.model_dump())
        await record(
            db,
            action="test_run.queued",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            metadata={
                "test_definition_id": str(run.test_definition_id),
                "correlation_id": str(run.correlation_id),
                "workspace_key": run.workspace_key,
            },
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _run_summary(run)


@router.get("/runs", response_model=list[TestRunSummary])
async def list_runs(
    ctx: RunReadContext,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    test_definition_id: UUID | None = Query(default=None),
    workspace_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
):
    stmt = select(TestRun).where(TestRun.tenant_id == ctx.tenant_id).order_by(TestRun.created_at.desc()).limit(limit)
    if status_filter:
        try:
            stmt = stmt.where(TestRun.status == TestRunStatus(status_filter))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid test run status") from exc
    if test_definition_id is not None:
        stmt = stmt.where(TestRun.test_definition_id == test_definition_id)
    if workspace_key is not None:
        stmt = stmt.where(TestRun.workspace_key == workspace_key)
    result = await db.execute(stmt)
    return [_run_summary(item) for item in result.scalars().all()]


@router.get("/runs/{run_id}", response_model=TestRunSummary)
async def get_run(run_id: UUID, ctx: RunReadContext, db: AsyncSession = Depends(get_db)):
    run = (await db.execute(select(TestRun).where(TestRun.id == run_id, TestRun.tenant_id == ctx.tenant_id))).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="test run not found")
    return _run_summary(run)


@router.post("/runs/{run_id}/start", response_model=TestRunSummary)
async def start_run(run_id: UUID, ctx: RunExecuteContext, db: AsyncSession = Depends(get_db)):
    service = TestCenterService(db)
    try:
        run = await service.start_run(run_id=run_id, tenant_id=ctx.tenant_id)
        await service.build_context(run.id, tenant_id=ctx.tenant_id)
        await record(
            db,
            action="test_run.started",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            metadata={"correlation_id": str(run.correlation_id)},
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _run_summary(run)


@router.post("/runs/{run_id}/finish", response_model=TestRunSummary)
async def finish_run(run_id: UUID, payload: TestRunFinish, ctx: RunExecuteContext, db: AsyncSession = Depends(get_db)):
    service = TestCenterService(db)
    try:
        run = await service.finish_run(run_id=run_id, tenant_id=ctx.tenant_id, **payload.model_dump())
        await record(
            db,
            action="test_run.passed" if payload.passed else "test_run.failed",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            status="success" if payload.passed else "failure",
            metadata={"correlation_id": str(run.correlation_id), "evidence_boundary": run.evidence_boundary},
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _run_summary(run)


@router.post("/runs/{run_id}/artifacts", response_model=TestRunArtifactSummary, status_code=status.HTTP_201_CREATED)
async def add_artifact(
    run_id: UUID,
    payload: TestRunArtifactCreate,
    ctx: RunExecuteContext,
    db: AsyncSession = Depends(get_db),
):
    service = TestCenterService(db)
    try:
        artifact = await service.add_artifact(run_id=run_id, tenant_id=ctx.tenant_id, **payload.model_dump())
        await record(
            db,
            action="test_run.artifact_added",
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
    return _artifact_summary(artifact)


@router.get("/runs/{run_id}/artifacts", response_model=list[TestRunArtifactSummary])
async def list_artifacts(run_id: UUID, ctx: RunReadContext, db: AsyncSession = Depends(get_db)):
    service = TestCenterService(db)
    try:
        artifacts = await service.list_artifacts(run_id=run_id, tenant_id=ctx.tenant_id)
    except TestCenterError as exc:
        raise _error(exc) from exc
    return [_artifact_summary(item) for item in artifacts]


@router.post("/runs/{run_id}/cancel", response_model=TestRunSummary)
async def cancel_run(run_id: UUID, ctx: RunExecuteContext, db: AsyncSession = Depends(get_db)):
    service = TestCenterService(db)
    try:
        run = await service.cancel_run(run_id=run_id, tenant_id=ctx.tenant_id)
        await record(
            db,
            action="test_run.cancelled",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            metadata={"correlation_id": str(run.correlation_id)},
        )
        await db.commit()
    except TestCenterError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _run_summary(run)
