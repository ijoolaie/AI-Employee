"""Safe Test Center execution boundary for P12.2-P12.4."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_definition import TestDefinition
from app.models.test_run import TestRun, TestRunStatus
from app.models.test_run_artifact import TestRunArtifact


class TestCenterError(RuntimeError):
    """Raised when a Test Center operation violates its execution contract."""


@dataclass(frozen=True)
class TestExecutionContext:
    tenant_id: uuid.UUID
    workspace_key: str | None
    actor_id: uuid.UUID | None
    correlation_id: uuid.UUID
    test_definition_id: uuid.UUID
    test_run_id: uuid.UUID


_FORBIDDEN_FIXTURE_KEYS = {"password", "passwd", "secret", "token", "api_key", "access_token", "refresh_token"}
_MAX_FIXTURE_KEYS = 100
_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def _safe_fixtures(fixtures: dict[str, Any] | None) -> dict[str, Any]:
    """Reject secret-bearing fixture keys instead of persisting credentials."""
    value = dict(fixtures or {})
    if len(value) > _MAX_FIXTURE_KEYS:
        raise TestCenterError("too many test fixture keys")
    for key in value:
        normalized = str(key).strip().lower().replace("-", "_")
        if normalized in _FORBIDDEN_FIXTURE_KEYS or any(part in normalized for part in ("password", "secret", "token")):
            raise TestCenterError("secret-bearing test fixtures are forbidden")
    return value


def _safe_sha256(value: str | None) -> str | None:
    if value is None:
        return None
    if not _SHA256_PATTERN.fullmatch(value):
        raise TestCenterError("artifact sha256 must be a 64-character hexadecimal digest")
    return value.lower()


class TestCenterService:
    """Tenant-bound application service; never accepts an untrusted tenant context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        test_definition_id: uuid.UUID,
        workspace_key: str | None = None,
        fixtures: dict[str, Any] | None = None,
    ) -> TestRun:
        definition = (
            await self.db.execute(
                select(TestDefinition).where(
                    TestDefinition.id == test_definition_id,
                    TestDefinition.tenant_id == tenant_id,
                    TestDefinition.enabled.is_(True),
                )
            )
        ).scalar_one_or_none()
        if definition is None:
            raise TestCenterError("test definition not found")
        if definition.workspace_key is not None and definition.workspace_key != workspace_key:
            raise TestCenterError("workspace boundary mismatch")

        run = TestRun(
            tenant_id=tenant_id,
            test_definition_id=definition.id,
            workspace_key=workspace_key,
            actor_id=actor_id,
            executor_type="backend",
            fixtures=_safe_fixtures(fixtures),
            status=TestRunStatus.QUEUED,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def build_context(self, run_id: uuid.UUID, *, tenant_id: uuid.UUID) -> TestExecutionContext:
        run = (
            await self.db.execute(
                select(TestRun).where(TestRun.id == run_id, TestRun.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        if run is None:
            raise TestCenterError("test run not found")
        return TestExecutionContext(
            tenant_id=run.tenant_id,
            workspace_key=run.workspace_key,
            actor_id=run.actor_id,
            correlation_id=run.correlation_id,
            test_definition_id=run.test_definition_id,
            test_run_id=run.id,
        )

    async def start_run(self, *, run_id: uuid.UUID, tenant_id: uuid.UUID) -> TestRun:
        run = await self._get_run_for_tenant(run_id, tenant_id, for_update=True)
        if run.status is not TestRunStatus.QUEUED:
            raise TestCenterError("only queued test runs can start")
        run.status = TestRunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run

    async def finish_run(
        self,
        *,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        passed: bool,
        result: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        error: str | None = None,
        runtime_version: str | None = None,
        migration_identity: str | None = None,
        git_sha: str | None = None,
    ) -> TestRun:
        run = await self._get_run_for_tenant(run_id, tenant_id, for_update=True)
        if run.status is not TestRunStatus.RUNNING:
            raise TestCenterError("only running test runs can finish")
        run.status = TestRunStatus.PASSED if passed else TestRunStatus.FAILED
        run.result = result or {}
        run.evidence = evidence or {}
        run.error = error
        run.runtime_version = runtime_version
        run.migration_identity = migration_identity
        run.git_sha = git_sha
        run.finished_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run

    async def add_artifact(
        self,
        *,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        artifact_type: str,
        label: str,
        reference: str,
        sha256: str | None = None,
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TestRunArtifact:
        run = await self._get_run_for_tenant(run_id, tenant_id, for_update=False)
        if run.status in {TestRunStatus.QUEUED, TestRunStatus.RUNNING}:
            raise TestCenterError("artifacts can only be attached to completed test runs")
        if not artifact_type.strip() or not label.strip() or not reference.strip():
            raise TestCenterError("artifact type, label and reference are required")
        if len(artifact_type) > 50 or len(label) > 255 or len(reference) > 2048:
            raise TestCenterError("artifact metadata exceeds allowed length")
        if size_bytes is not None and size_bytes < 0:
            raise TestCenterError("artifact size cannot be negative")
        artifact = TestRunArtifact(
            tenant_id=tenant_id,
            test_run_id=run.id,
            artifact_type=artifact_type.strip(),
            label=label.strip(),
            reference=reference.strip(),
            sha256=_safe_sha256(sha256),
            size_bytes=size_bytes,
            metadata=dict(metadata or {}),
        )
        self.db.add(artifact)
        await self.db.flush()
        return artifact

    async def list_artifacts(self, *, run_id: uuid.UUID, tenant_id: uuid.UUID) -> list[TestRunArtifact]:
        await self._get_run_for_tenant(run_id, tenant_id, for_update=False)
        result = await self.db.execute(
            select(TestRunArtifact)
            .where(TestRunArtifact.test_run_id == run_id, TestRunArtifact.tenant_id == tenant_id)
            .order_by(TestRunArtifact.created_at.asc())
        )
        return list(result.scalars().all())

    async def cancel_run(self, *, run_id: uuid.UUID, tenant_id: uuid.UUID) -> TestRun:
        run = await self._get_run_for_tenant(run_id, tenant_id, for_update=True)
        if run.status in {TestRunStatus.PASSED, TestRunStatus.FAILED, TestRunStatus.CANCELLED, TestRunStatus.EXPIRED}:
            raise TestCenterError("terminal test run cannot be cancelled")
        run.status = TestRunStatus.CANCELLED
        run.finished_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run

    async def _get_run_for_tenant(self, run_id: uuid.UUID, tenant_id: uuid.UUID, *, for_update: bool) -> TestRun:
        stmt = select(TestRun).where(TestRun.id == run_id, TestRun.tenant_id == tenant_id)
        if for_update:
            stmt = stmt.with_for_update()
        run = (await self.db.execute(stmt)).scalar_one_or_none()
        if run is None:
            raise TestCenterError("test run not found")
        return run
