from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.workers import run_worker


@contextmanager
def _span(*_args, **_kwargs):
    yield


class _Db:
    def __init__(self, run, version):
        self.run = run
        self.version = version
        self.committed = False

    async def execute(self, query):
        text = str(query)
        if "employee_versions" in text:
            return SimpleNamespace(scalar_one_or_none=lambda: self.version)
        if "tool_approval_requests" in text:
            return SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))
        return SimpleNamespace(scalar_one_or_none=lambda: self.run)

    async def commit(self):
        self.committed = True


@asynccontextmanager
async def _session(db):
    yield db


def _run(run_id, tenant_id):
    return SimpleNamespace(
        id=run_id,
        tenant_id=tenant_id,
        employee_id=uuid4(),
        employee_version_id=uuid4(),
        input_data={},
    )


def test_execute_run_task_requires_tenant_context():
    with pytest.raises(ValidationAppError):
        run_worker.execute_run_task(str(uuid4()), "")


def test_execute_run_task_rejects_invalid_context():
    with pytest.raises(ValidationAppError):
        run_worker.execute_run_task("not-a-uuid", str(uuid4()))


@pytest.mark.asyncio
async def test_run_worker_fails_closed_on_tenant_mismatch(monkeypatch):
    run_id = uuid4()
    owner_tenant = uuid4()
    supplied_tenant = uuid4()
    db = _Db(_run(run_id, owner_tenant), SimpleNamespace(rules={}))

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)

    with pytest.raises(ValidationAppError):
        await run_worker._run_async(str(run_id), str(supplied_tenant))

    assert db.committed is False


@pytest.mark.asyncio
async def test_run_worker_passes_matching_tenant_to_run_service(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    run = _run(run_id, tenant_id)
    db = _Db(run, SimpleNamespace(rules={}))
    calls = []

    async def _execute(db_arg, *, run_id):
        calls.append((db_arg, run_id))

    async def _memory(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)

    await run_worker._run_async(str(run_id), str(tenant_id))

    assert calls == [(db, run_id)]
    assert db.committed is True


@pytest.mark.asyncio
async def test_run_worker_commits_failure_before_reraising(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    run = _run(run_id, tenant_id)
    db = _Db(run, SimpleNamespace(rules={}))

    async def _execute(_db_arg, *, run_id):
        raise RuntimeError(f"execution failed: {run_id}")

    async def _memory(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)

    with pytest.raises(RuntimeError, match="execution failed"):
        await run_worker._run_async(str(run_id), str(tenant_id))

    assert db.committed is True
