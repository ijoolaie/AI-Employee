"""P12.6 exportable verification record contract tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.test_run import TestRunStatus
from app.services.test_center_verification import (
    TestCenterVerificationService,
    VerificationRecordError,
)


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value or []


class VerificationFakeDB:
    def __init__(self, run, definition, artifacts):
        self.values = [run, definition, artifacts]
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return Result(self.values.pop(0))


@pytest.mark.asyncio
async def test_verification_record_is_complete_and_excludes_fixtures():
    tenant_id = uuid4()
    run_id = uuid4()
    definition_id = uuid4()
    now = datetime.now(timezone.utc)
    run = type("Run", (), {
        "id": run_id,
        "tenant_id": tenant_id,
        "test_definition_id": definition_id,
        "workspace_key": "ops",
        "status": TestRunStatus.PASSED,
        "actor_id": uuid4(),
        "executor_type": "backend",
        "correlation_id": uuid4(),
        "queued_at": now,
        "started_at": now,
        "finished_at": now,
        "created_at": now,
        "result": {"checks": 3},
        "error": None,
        "evidence": {"log": "available"},
        "runtime_version": "python-3.12",
        "migration_identity": "p12_04_test_evidence",
        "git_sha": "a" * 64,
        "evidence_boundary": "engineering_product_evidence",
        "fixtures": {"customer_id": "demo"},
    })()
    definition = type("Definition", (), {
        "id": definition_id,
        "tenant_id": tenant_id,
        "code": "smoke.checkout",
        "name": "Checkout smoke",
        "test_type": "acceptance",
        "category": "backend",
        "description": "Checkout smoke test",
        "workspace_key": "ops",
        "prerequisites": {"seeded": True},
        "expected_result": {"passed": True},
        "evidence_requirements": {"log": True},
        "enabled": True,
        "created_at": now,
        "updated_at": now,
    })()
    artifact = type("Artifact", (), {
        "id": uuid4(),
        "artifact_type": "log",
        "label": "pytest",
        "reference": "artifacts/pytest.log",
        "sha256": "b" * 64,
        "size_bytes": 42,
        "metadata": {"format": "text"},
        "created_at": now,
    })()
    db = VerificationFakeDB(run, definition, [artifact])

    record = await TestCenterVerificationService(db).build_record(tenant_id=tenant_id, run_id=run_id)

    assert record["record_type"] == "test_center_verification_record"
    assert record["schema_version"] == "1.0"
    assert record["acceptance_boundary"] == "engineering_product_evidence"
    assert record["run"]["git_sha"] == "a" * 64
    assert record["test_definition"]["code"] == "smoke.checkout"
    assert record["artifacts"][0]["sha256"] == "b" * 64
    assert "fixtures" not in record["run"]


@pytest.mark.asyncio
async def test_verification_record_rejects_cross_tenant_run():
    db = VerificationFakeDB(None, None, [])
    with pytest.raises(VerificationRecordError, match="test run not found"):
        await TestCenterVerificationService(db).build_record(tenant_id=uuid4(), run_id=uuid4())


@pytest.mark.asyncio
async def test_verification_record_requires_passed_or_failed_run():
    tenant_id = uuid4()
    run = type("Run", (), {"id": uuid4(), "tenant_id": tenant_id, "status": TestRunStatus.RUNNING})()
    db = VerificationFakeDB(run, None, [])
    with pytest.raises(VerificationRecordError, match="completed"):
        await TestCenterVerificationService(db).build_record(tenant_id=tenant_id, run_id=run.id)
