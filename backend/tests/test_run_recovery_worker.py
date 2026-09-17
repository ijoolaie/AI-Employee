from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.workers import run_recovery_worker


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._rows))


class _Db:
    def __init__(self, rows):
        self.rows = rows
        self.committed = False

    async def execute(self, _statement):
        return _Result(self.rows)

    async def commit(self):
        self.committed = True


class _Session:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_sweep_recovers_stale_runs(monkeypatch):
    runs = [SimpleNamespace(id=uuid4(), status="running") for _ in range(2)]
    db = _Db(runs)
    calls = []

    def _session():
        return _Session(db)

    async def _recover(_db, *, run):
        calls.append(run.id)
        return run.id == runs[0].id

    monkeypatch.setattr(run_recovery_worker, "worker_db_session", _session)
    monkeypatch.setattr(run_recovery_worker, "recover_stale_run_execution", _recover)

    assert await run_recovery_worker._recover_stale_runs_async() == 1
    assert calls == [runs[0].id, runs[1].id]
    assert db.committed is True


@pytest.mark.asyncio
async def test_sweep_commits_even_when_no_stale_runs(monkeypatch):
    db = _Db([])

    monkeypatch.setattr(run_recovery_worker, "worker_db_session", lambda: _Session(db))

    assert await run_recovery_worker._recover_stale_runs_async() == 0
    assert db.committed is True
