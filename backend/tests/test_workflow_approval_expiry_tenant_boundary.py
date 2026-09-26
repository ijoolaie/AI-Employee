from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.workers import workflow_trigger_worker


class _ScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values

    def scalar_one_or_none(self):
        return self.values[0] if self.values else None


class _DbContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDb:
    def __init__(self, approval, step, run):
        self.results = iter([
            _ScalarResult([approval]),
            _ScalarResult([step]),
            _ScalarResult([run]),
        ])

    async def execute(self, _statement):
        return next(self.results)

    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_approval_expiry_does_not_cross_tenant_or_step_boundary(monkeypatch):
    approval = SimpleNamespace(
        status="pending",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        decided_at=None,
        workflow_step_run_id="step-b",
        workflow_run_id="run-b",
        tenant_id="tenant-a",
        id="approval-a",
        step_key="approve",
    )
    step = SimpleNamespace(workflow_run_id="run-b", status="waiting", error=None, completed_at=None)
    run = SimpleNamespace(id="run-b", tenant_id="tenant-b", status="waiting_approval", error=None, completed_at=None)
    db = _FakeDb(approval, step, run)

    import app.core.database as database
    import app.services.audit_service as audit_service

    monkeypatch.setattr(database, "worker_db_session", lambda: _DbContext(db))
    monkeypatch.setattr(audit_service, "record", AsyncMock())

    count = await workflow_trigger_worker._expire_workflow_approvals_async()

    assert count == 1
    assert approval.status == "expired"
    assert run.status == "waiting_approval"
    assert step.status == "waiting"
