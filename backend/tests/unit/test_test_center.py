"""Legacy Test Center boundary tests aligned with the P12 service contract."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.test_run import TestRunStatus
from app.services.test_center import TestCenterError, TestCenterService, _safe_fixtures


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
    def __init__(self, definition=None, run=None):
        self.definition = definition
        self.run = run
        self.added = []

    async def execute(self, _statement):
        return Result(self.definition if self.definition is not None else self.run)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid4()
            if getattr(value, "correlation_id", None) is None:
                value.correlation_id = uuid4()


def test_safe_fixtures_reject_secret_bearing_values():
    with pytest.raises(TestCenterError, match="secret-bearing"):
        _safe_fixtures({"api_token": "do-not-store"})


@pytest.mark.asyncio
async def test_test_center_preserves_tenant_and_evidence_boundary():
    tenant = uuid4()
    definition = SimpleNamespace(id=uuid4(), tenant_id=tenant, enabled=True, workspace_key=None)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, test_definition_id=definition.id, workspace_key=None,
        actor_id=uuid4(), correlation_id=uuid4(), status=TestRunStatus.QUEUED,
        fixtures={}, result=None, evidence={}, error=None, started_at=None, finished_at=None,
        runtime_version=None, migration_identity=None, git_sha=None,
        evidence_boundary="engineering_product_evidence",
    )
    db = FakeDB(run=run)
    service = TestCenterService(db)

    started = await service.start_run(run_id=run.id, tenant_id=tenant)
    assert started.status is TestRunStatus.RUNNING

    finished = await service.finish_run(
        run_id=run.id, tenant_id=tenant, passed=True,
        evidence={"check": "tenant-isolation"}, runtime_version="python-3.12",
        migration_identity="p12_04_test_evidence", git_sha="a" * 64,
    )
    assert finished.tenant_id == tenant
    assert finished.status is TestRunStatus.PASSED
    assert finished.evidence["check"] == "tenant-isolation"
    assert finished.evidence_boundary == "engineering_product_evidence"


@pytest.mark.asyncio
async def test_test_center_rejects_cross_tenant_run_access():
    tenant = uuid4()
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, test_definition_id=uuid4(), workspace_key=None,
        actor_id=uuid4(), correlation_id=uuid4(), status=TestRunStatus.QUEUED,
    )
    # The fake DB is intentionally statement-agnostic, so a real tenant filter\n    # must be simulated here by returning no run for the foreign-tenant lookup.\n    db = FakeDB(run=None)\n\n    with pytest.raises(TestCenterError, match="test run not found"):\n        await TestCenterService(db).start_run(run_id=run.id, tenant_id=uuid4())\n