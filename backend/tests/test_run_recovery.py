from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.ai_provider_call import AIProviderCall
from app.services import run_recovery


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._rows))


class _Db:
    def __init__(self, rows):
        self.rows = rows
        self.flushed = False

    async def execute(self, _statement):
        return _Result(self.rows)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_fresh_running_run_is_not_recovered(monkeypatch):
    run = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        request_id=None,
        status="running",
        started_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        completed_at=None,
        error_message=None,
    )
    db = _Db([])

    assert await run_recovery.recover_stale_run_execution(db, run=run) is False
    assert run.status == "running"
    assert db.flushed is False


@pytest.mark.asyncio
async def test_stale_running_run_marks_inflight_provider_call_unknown(monkeypatch):
    run = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        request_id=None,
        status="running",
        started_at=datetime.now(timezone.utc) - timedelta(seconds=run_recovery.STALE_RUN_RECOVERY_SECONDS + 1),
        completed_at=None,
        error_message=None,
    )
    call = AIProviderCall(
        tenant_id=run.tenant_id,
        run_id=None,
        provider="lm_studio",
        model="google/gemma-4e4b",
        status="in_flight",
        raw_meta={"logical_run_id": str(run.id), "logical_turn": "1"},
    )
    db = _Db([call])
    audits = []

    async def _audit(*_args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(run_recovery.audit_service, "record", _audit)

    recovered = await run_recovery.recover_stale_run_execution(db, run=run)

    assert recovered is True
    assert run.status == "failed"
    assert run.completed_at is not None
    assert "ambiguous" in run.error_message.lower()
    assert call.status == "unknown"
    assert call.error_message
    assert call.raw_meta["ambiguous_provider_outcome"] is True
    assert call.raw_meta["recovered_from_stale_worker"] is True
    assert db.flushed is True
    assert audits[0]["action"] == "run.execution_recovered"
    assert audits[0]["metadata"]["replay_blocked"] is True


@pytest.mark.asyncio
async def test_stale_running_run_without_inflight_call_still_fails_closed(monkeypatch):
    run = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        request_id=None,
        status="running",
        started_at=datetime.now(timezone.utc) - timedelta(seconds=run_recovery.STALE_RUN_RECOVERY_SECONDS + 1),
        completed_at=None,
        error_message=None,
    )
    db = _Db([])

    async def _audit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(run_recovery.audit_service, "record", _audit)

    assert await run_recovery.recover_stale_run_execution(db, run=run) is True
    assert run.status == "failed"
    assert run.completed_at is not None
    assert "replay was intentionally blocked" in run.error_message
