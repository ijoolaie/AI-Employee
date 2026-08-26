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
    def __init__(self, run):
        self.run = run
        self.committed = False

    async def execute(self, _query):
        return SimpleNamespace(scalar_one_or_none=lambda: self.run)

    async def commit(self):
        self.committed = True


@asynccontextmanager
async def _session(db):
    yield db


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
    db = _Db(SimpleNamespace(id=run_id, tenant_id=owner_tenant))

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)

    with pytest.raises(ValidationAppError):
        await run_worker._run_async(str(run_id), str(supplied_tenant))

    assert db.committed is False


@pytest.mark.asyncio
async def test_run_worker_passes_matching_tenant_to_run_service(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    db = _Db(SimpleNamespace(id=run_id, tenant_id=tenant_id))
    calls = []

    async def _execute(db_arg, *, run_id):
        calls.append((db_arg, run_id))

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)

    await run_worker._run_async(str(run_id), str(tenant_id))

    assert calls == [(db, run_id)]
    assert db.committed is True
