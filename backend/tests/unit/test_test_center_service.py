"""P12.1-P12.5 Test Center service contract tests."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.test_run import TestRunStatus
from app.services.test_center import TestCenterError, TestCenterService, _safe_fixtures


def test_secret_bearing_fixtures_are_rejected():
    with pytest.raises(TestCenterError, match="secret-bearing"):
        _safe_fixtures({"api_token": "do-not-store"})


def test_fixture_shape_is_preserved_when_safe():
    assert _safe_fixtures({"customer_id": "demo", "quantity": 2}) == {"customer_id": "demo", "quantity": 2}


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value or []


class FakeDB:
    def __init__(self, definition=None, run=None, artifacts=None):
        self.definition = definition
        self.run = run
        self.artifacts = artifacts or []
        self.added = []

    async def execute(self, _statement):
        if self.artifacts:
            return Result(self.artifacts)
        return Result(self.definition if self.definition is not None else self.run)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid4()
            if getattr(value, "correlation_id", None) is None:
                value.correlation_id = uuid4()


class HistoryFakeDB:
    def __init__(self, runs):
        self.runs = runs
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return Result(self.runs)


@pytest.mark.asyncio
async def test_create_run_is_tenant_bound_and_queued():
    tenant_id = uuid4()
    definition = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True, workspace_key="ops")
    db = FakeDB(definition=definition)
    run = await TestCenterService(db).create_run(
        tenant_id=tenant_id,
        actor_id=uuid4(),
        test_definition_id=definition.id,
        workspace_key="ops",
        fixtures={"case": "smoke"},
    )
    assert run.tenant_id == tenant_id
    assert run.test_definition_id == definition.id
    assert run.status is TestRunStatus.QUEUED
    assert run.fixtures == {"case": "smoke"}


@pytest.mark.asyncio
async def test_cross_tenant_definition_is_not_resolvable():
    tenant_id = uuid4()
    other_tenant = uuid4()
    definition = SimpleNamespace(id=uuid4(), tenant_id=other_tenant, enabled=True, workspace_key=None)
    db = FakeDB(definition=None)
    with pytest.raises(TestCenterError, match="test definition not found"):
        await TestCenterService(db).create_run(tenant_id=tenant_id, actor_id=uuid4(), test_definition_id=definition.id)


@pytest.mark.asyncio
async def test_run_lifecycle_is_queued_running_passed():
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, test_definition_id=uuid4(), workspace_key=None,
        actor_id=uuid4(), correlation_id=uuid4(), status=TestRunStatus.QUEUED,
        fixtures={}, result=None, evidence={}, error=None, started_at=None, finished_at=None,
        queued_at=now, runtime_version=None, migration_identity=None, git_sha=None,
        evidence_boundary="engineering_product_evidence",
    )
    db = FakeDB(run=run)
    service = TestCenterService(db)
    started = await service.start_run(run_id=run.id, tenant_id=tenant_id)
    assert started.status is TestRunStatus.RUNNING
    finished = await service.finish_run(
        run_id=run.id, tenant_id=tenant_id, passed=True,
        result={"checks": 1}, evidence={"boundary": "engineering_product_evidence"},
        runtime_version="python-3.12", migration_identity="p12_04_test_evidence", git_sha="a" * 64,
    )
    assert finished.status is TestRunStatus.PASSED
    assert finished.result == {"checks": 1}
    assert finished.runtime_version == "python-3.12"
    assert finished.migration_identity == "p12_04_test_evidence"
    assert finished.git_sha == "a" * 64


@pytest.mark.asyncio
async def test_expired_transition_is_time_bound_and_terminal():
    tenant_id = uuid4()
    queued_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.QUEUED,
        queued_at=queued_at, started_at=None, finished_at=None, error=None,
    )
    db = FakeDB(run=run)
    service = TestCenterService(db)
    with pytest.raises(TestCenterError, match="has not expired"):
        await service.expire_run(
            run_id=run.id, tenant_id=tenant_id, timeout_seconds=60,
            now=queued_at + timedelta(seconds=59),
        )
    expired = await service.expire_run(
        run_id=run.id, tenant_id=tenant_id, timeout_seconds=60,
        now=queued_at + timedelta(seconds=60),
    )
    assert expired.status is TestRunStatus.EXPIRED
    assert expired.finished_at == queued_at + timedelta(seconds=60)
    assert expired.error == "test run expired"
    with pytest.raises(TestCenterError, match="terminal"):
        await service.expire_run(
            run_id=run.id, tenant_id=tenant_id, timeout_seconds=60,
            now=queued_at + timedelta(seconds=120),
        )


@pytest.mark.asyncio
async def test_running_expiration_uses_started_at():
    tenant_id = uuid4()
    started_at = datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.RUNNING,
        queued_at=started_at - timedelta(hours=1), started_at=started_at,
        finished_at=None, error=None,
    )
    db = FakeDB(run=run)
    expired = await TestCenterService(db).expire_run(
        run_id=run.id, tenant_id=tenant_id, timeout_seconds=30,
        now=started_at + timedelta(seconds=30),
    )
    assert expired.status is TestRunStatus.EXPIRED


@pytest.mark.asyncio
async def test_history_is_tenant_scoped_and_filters_are_composed():
    tenant_id = uuid4()
    definition_id = uuid4()
    now = datetime.now(timezone.utc)
    runs = [
        SimpleNamespace(id=uuid4(), tenant_id=tenant_id, test_definition_id=definition_id, workspace_key="ops", status=TestRunStatus.PASSED, created_at=now),
        SimpleNamespace(id=uuid4(), tenant_id=tenant_id, test_definition_id=definition_id, workspace_key="ops", status=TestRunStatus.FAILED, created_at=now - timedelta(hours=2)),
    ]
    db = HistoryFakeDB(runs)
    result = await TestCenterService(db).list_history(
        tenant_id=tenant_id,
        workspace_key="ops",
        test_definition_id=definition_id,
        status=TestRunStatus.PASSED,
        created_after=now - timedelta(days=1),
        created_before=now + timedelta(minutes=1),
        limit=20,
    )
    assert result == runs
    sql = str(db.statement)
    assert "test_runs.tenant_id" in sql
    assert "test_runs.workspace_key" in sql
    assert "test_runs.test_definition_id" in sql
    assert "test_runs.status" in sql
    assert "test_runs.created_at" in sql


@pytest.mark.asyncio
async def test_history_rejects_invalid_date_range_and_pagination():
    tenant_id = uuid4()
    db = HistoryFakeDB([])
    now = datetime.now(timezone.utc)
    service = TestCenterService(db)
    with pytest.raises(TestCenterError, match="date range"):
        await service.list_history(tenant_id=tenant_id, created_after=now, created_before=now - timedelta(seconds=1))
    with pytest.raises(TestCenterError, match="limit"):
        await service.list_history(tenant_id=tenant_id, limit=201)
    with pytest.raises(TestCenterError, match="offset"):
        await service.list_history(tenant_id=tenant_id, offset=-1)


@pytest.mark.asyncio
async def test_artifact_sha256_and_terminal_boundary_are_enforced():
    tenant_id = uuid4()
    run = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.PASSED)
    db = FakeDB(run=run)
    service = TestCenterService(db)
    with pytest.raises(TestCenterError, match="sha256"):
        await service.add_artifact(run_id=run.id, tenant_id=tenant_id, artifact_type="log", label="pytest", reference="artifacts/pytest.log", sha256="not-a-digest")
    artifact = await service.add_artifact(
        run_id=run.id, tenant_id=tenant_id, artifact_type="log", label="pytest", reference="artifacts/pytest.log",
        sha256="A" * 64, size_bytes=42, metadata={"format": "text"},
    )
    assert artifact.tenant_id == tenant_id
    assert artifact.test_run_id == run.id
    assert artifact.sha256 == "a" * 64
    assert artifact.size_bytes == 42


@pytest.mark.asyncio
async def test_artifact_cannot_be_attached_to_active_run():
    tenant_id = uuid4()
    run = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.RUNNING)
    db = FakeDB(run=run)
    with pytest.raises(TestCenterError, match="completed"):
        await TestCenterService(db).add_artifact(run_id=run.id, tenant_id=tenant_id, artifact_type="log", label="pytest", reference="artifacts/pytest.log")
