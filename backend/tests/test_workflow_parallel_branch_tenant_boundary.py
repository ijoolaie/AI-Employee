from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import workflow_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _DbContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDb:
    def __init__(self, branch, parent):
        self.values = iter([_Result(branch), _Result(parent)])

    async def execute(self, _statement):
        return next(self.values)


@pytest.mark.asyncio
async def test_parallel_branch_rejects_cross_tenant_before_lease(monkeypatch):
    branch = SimpleNamespace(workflow_run_id="run-a")
    parent = SimpleNamespace(
        tenant_id="tenant-a",
        status="pending",
    )
    db = _FakeDb(branch, parent)
    acquire_lease = AsyncMock()

    import app.core.database as database
    import app.services.workflow_execution_lease as lease_service

    monkeypatch.setattr(database, "worker_db_session", lambda: _DbContext(db))
    monkeypatch.setattr(lease_service, "acquire_parallel_branch_execution_lease", acquire_lease)

    with pytest.raises(
        workflow_service.ValidationAppError,
        match="Worker tenant context does not match Workflow Run tenant",
    ):
        await workflow_service._execute_parallel_branch(
            "branch-a",
            expected_tenant_id="tenant-b",
        )

    acquire_lease.assert_not_awaited()
