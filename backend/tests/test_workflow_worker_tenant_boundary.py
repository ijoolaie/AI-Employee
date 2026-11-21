from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.workers import workflow_worker


class _FakeDb:
    def __init__(self, durable_tenant_id, task_tenant_id):
        self._durable_tenant_id = durable_tenant_id
        self._task_tenant_id = task_tenant_id
        self.queries = []

    async def execute(self, statement):
        self.queries.append(str(statement))
        return SimpleNamespace(
            scalar_one_or_none=lambda: (
                self._durable_tenant_id
                if self._durable_tenant_id is not None
                and self._durable_tenant_id == self._task_tenant_id
                else None
            )
        )

    async def commit(self):
        raise AssertionError("tenant validation failure must not commit")

    async def rollback(self):
        pass


class _DbContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("durable_tenant_id", "task_tenant_id", "message"),
    [
        ("10000000-0000-0000-0000-000000000001", "20000000-0000-0000-0000-000000000002", "Workflow Run not found for tenant context"),
        (None, "10000000-0000-0000-0000-000000000001", "Workflow Run not found for tenant context"),
    ],
)
async def test_workflow_worker_validates_durable_tenant_before_execution(
    monkeypatch,
    durable_tenant_id,
    task_tenant_id,
    message,
):
    db = _FakeDb(durable_tenant_id, task_tenant_id)
    acquire_lease = AsyncMock()
    execute_workflow = AsyncMock()

    monkeypatch.setattr(
        workflow_worker,
        "worker_db_session",
        lambda: _DbContext(db),
    )
    monkeypatch.setattr(
        workflow_worker.workflow_service,
        "acquire_workflow_execution_lease",
        acquire_lease,
    )
    monkeypatch.setattr(
        workflow_worker.workflow_service,
        "execute_workflow",
        execute_workflow,
    )

    with pytest.raises(ValueError, match=message):
        await workflow_worker._run_async(
            "00000000-0000-0000-0000-000000000001",
            task_tenant_id,
        )

    assert len(db.queries) == 1
    assert "workflow_runs.tenant_id =" in db.queries[0]
    acquire_lease.assert_not_awaited()
    execute_workflow.assert_not_awaited()
