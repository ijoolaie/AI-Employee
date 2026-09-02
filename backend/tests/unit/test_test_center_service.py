"""P12.1-P12.4 Test Center service contract tests."""

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


@pytest.mark.asyncio
async def test_create_run_is_tenant_bound_and_queued():
    tenant_id = uuid4()
    definition = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, enabled=True, workspace_key="ops"
    )
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
    definition = SimpleNamespace(
        id=uuid4(), tenant_id=other_tenant, enabled=True, workspace_key=None
    )
    db = FakeDB(definition=None)
    with pytest.raises(TestCenterError, match="test definition not found"):
        await TestCenterService(db).create_run(
            tenant_id=tenant_id,
            actor_id=uuid4(),
            test_definition_id=definition.id,
        )


@pytest.mark.asyncio
async def test_run_lifecycle_is_queued_running_passed():
    tenant_id = uuid4()
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, test_definition_id=uuid4(), workspace_key=None,
        actor_id=uuid4(), correlation_id=uuid4(), status=TestRunStatus.QUEUED,
        fixtures={}, result=None, evidence={}, error=None, started_at=None, finished_at=None,
        runtime_version=None, migration_identity=None, git_sha=None,
        evidence_boundary="engineering_product_evidence",
    )
    db = FakeDB(run=run)
    service = TestCenterService(db)
    started = await service.start_run(run_id=run.id, tenant_id=tenant_id)
    assert started.status is TestRunStatus.RUNNING
    finished = await service.finish_run(
        run_id=run.id, tenant_id=tenant_id, passed=True,
        result={"checks": 1}, evidence={"boundary": "engineering_product_evidence"},
        runtime_version="python-3.12", migration_identity="p12_04_test_evidence",
        git_sha="a" * 64,
    )
    assert finished.status is TestRunStatus.PASSED
    assert finished.result == {"checks": 1}
    assert finished.runtime_version == "python-3.12"
    assert finished.migration_identity == "p12_04_test_evidence"
    assert finished.git_sha == "a" * 64


@pytest.mark.asyncio
async def test_artifact_sha256_and_terminal_boundary_are_enforced():
    tenant_id = uuid4()
    run = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.PASSED)
    db = FakeDB(run=run)
    service = TestCenterService(db)

    with pytest.raises(TestCenterError, match="sha256"):
        await service.add_artifact(
            run_id=run.id,
            tenant_id=tenant_id,
            artifact_type="log",
            label="pytest",
            reference="artifacts/pytest.log",
            sha256="not-a-digest",
        )

    artifact = await service.add_artifact(
        run_id=run.id,
        tenant_id=tenant_id,
        artifact_type="log",
        label="pytest",
        reference="artifacts/pytest.log",
        sha256="A" * 64,
        size_bytes=42,
        metadata={"format": "text"},
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
        await TestCenterService(db).add_artifact(
            run_id=run.id,
            tenant_id=tenant_id,
            artifact_type="log",
            label="pytest",
            reference="artifacts/pytest.log",
        )
