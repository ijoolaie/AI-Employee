from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.workers import test_center_worker, workflow_trigger_worker


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows

    def scalar_one_or_none(self):
        return self.rows[0] if self.rows else None


class _Db:
    def __init__(self, results=()):
        self.results = iter(results)
        self.committed = False
        self.flushed = False

    async def execute(self, _statement):
        return _Result(next(self.results))

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


@asynccontextmanager
async def _session(db):
    yield db


@pytest.mark.asyncio
async def test_test_center_global_expiration_sweep_audits_each_run_under_its_own_tenant(monkeypatch):
    runs = [
        SimpleNamespace(id=uuid4(), tenant_id=uuid4(), correlation_id=uuid4()),
        SimpleNamespace(id=uuid4(), tenant_id=uuid4(), correlation_id=uuid4()),
    ]
    db = _Db()
    audits = []

    async def _expire(self, **_kwargs):
        return runs

    async def _record(_db, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(test_center_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(test_center_worker, "get_settings", lambda: SimpleNamespace(test_center_run_timeout_seconds=60))
    monkeypatch.setattr(test_center_worker.TestCenterService, "expire_stale_runs", _expire)
    monkeypatch.setattr(test_center_worker, "record", _record)

    assert await test_center_worker._expire_stale_runs_async() == 2
    assert [entry["tenant_id"] for entry in audits] == [run.tenant_id for run in runs]
    assert [entry["resource_id"] for entry in audits] == [run.id for run in runs]
    assert db.committed is True


@pytest.mark.asyncio
async def test_workflow_timeout_sweeper_keeps_audit_attribution_per_run_tenant(monkeypatch):
    now = datetime.now(timezone.utc)
    runs = [
        SimpleNamespace(id=uuid4(), tenant_id=uuid4(), status="running", deadline_at=now - timedelta(seconds=5), completed_at=None, error=None),
        SimpleNamespace(id=uuid4(), tenant_id=uuid4(), status="waiting_approval", deadline_at=now - timedelta(seconds=5), completed_at=None, error=None),
    ]
    db = _Db(results=[[], [], runs, [], []])
    audit_record = AsyncMock()

    @asynccontextmanager
    async def _db_session():
        yield db

    import app.core.database as database
    import app.services.audit_service as audit_service

    monkeypatch.setattr(workflow_trigger_worker, "worker_db_session", _db_session)
    monkeypatch.setattr(database, "worker_db_session", _db_session)
    monkeypatch.setattr(audit_service, "record", audit_record)

    assert await workflow_trigger_worker._timeout_workflow_runs_async() == 2
    assert [call.kwargs["tenant_id"] for call in audit_record.await_args_list] == [run.tenant_id for run in runs]
    assert [run.status for run in runs] == ["timed_out", "timed_out"]
    assert db.committed is True
