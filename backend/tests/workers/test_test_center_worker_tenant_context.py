from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.test_center import TestCenterError
from app.workers import test_center_worker


class _Db:
    def __init__(self):
        self.queries = []

    async def execute(self, query):
        self.queries.append(str(query))
        return SimpleNamespace(scalar_one_or_none=lambda: None)


@asynccontextmanager
async def _session(db):
    yield db


@pytest.mark.asyncio
async def test_test_center_worker_scopes_run_lookup_to_dispatched_tenant(monkeypatch):
    db = _Db()
    monkeypatch.setattr(test_center_worker, "worker_db_session", lambda: _session(db))

    with pytest.raises(TestCenterError, match="test run not found"):
        await test_center_worker._execute_run_async(uuid4(), uuid4())

    assert len(db.queries) == 1
    assert "test_runs.tenant_id =" in db.queries[0]


def test_test_center_task_rejects_invalid_tenant_context():
    with pytest.raises(ValueError):
        test_center_worker.execute_run_task(str(uuid4()), "not-a-tenant-uuid")


def test_test_center_api_dispatches_expected_tenant():
    from pathlib import Path

    source = (Path(__file__).parents[2] / "app/api/v1/test_center_execution.py").read_text()
    assert "execute_run_task.delay(str(run.id), str(ctx.tenant_id))" in source
