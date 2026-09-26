from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.workers import workflow_worker


class _FakeDb:
    def __init__(self, durable_tenant_id):
        self._durable_tenant_id = durable_tenant_id

    async def execute(self, _statement):
        return SimpleNamespace(scalar_one_or_none=lambda: self._durable_tenant_id)

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
        ("tenant-a", "tenant-b", "Worker tenant context does not match Workflow Run tenant"),
        (None, "tenant-a", "Workflow Run not found"),
    ],
)
async def test_workflow_worker_validates_durable_tenant_before_execution(
    monkeypatch,
    durable_tenant_id,
    task_tenant_id,
    message,
):
    db = _FakeDb(durable_tenant_id)
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

    acquire_lease.assert_not_awaited()
    execute_workflow.assert_not_awaited()
