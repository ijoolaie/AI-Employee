from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.ai_provider_call import AIProviderCall
from app.services import run_recovery


class _Result:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._rows))

    def scalar_one_or_none(self):
        return self._scalar


class _Db:
    def __init__(self, *, locked_run, provider_calls):
        self.locked_run = locked_run
        self.provider_calls = provider_calls
        self.execute_calls = 0
        self.flushed = False

    async def execute(self, _statement):
        self.execute_calls += 1
        if self.execute_calls == 1:
            return _Result(scalar=self.locked_run)
        return _Result(rows=self.provider_calls)

    async def flush(self):
        self.flushed = True


def _run(*, started_seconds_ago: int):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        request_id=None,
        status="running",
        started_at=datetime.now(timezone.utc) - timedelta(seconds=started_seconds_ago),
        completed_at=None,
        error_message=None,
        total_tokens=0,
        total_cost_usd=0,
    )


@pytest.mark.asyncio
async def test_fresh_running_run_is_not_recovered():
    run = _run(started_seconds_ago=30)
    db = _Db(locked_run=run, provider_calls=[])

    assert await run_recovery.recover_stale_run_execution(db, run=run) is False
    assert run.status == "running"
    assert db.flushed is False
    assert db.execute_calls == 0


@pytest.mark.asyncio
async def test_stale_running_run_marks_inflight_provider_call_unknown(monkeypatch):
    run = _run(started_seconds_ago=run_recovery.STALE_RUN_RECOVERY_SECONDS + 1)
    call = AIProviderCall(
        tenant_id=run.tenant_id,
        run_id=None,
        provider="lm_studio",
        model="google/gemma-4e4b",
        status="in_flight",
        raw_meta={"logical_run_id": str(run.id), "logical_turn": "1"},
    )
    db = _Db(locked_run=run, provider_calls=[call])
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
    assert db.execute_calls == 2
    assert audits[0]["action"] == "run.execution_recovered"
    assert audits[0]["metadata"]["replay_blocked"] is True


@pytest.mark.asyncio
async def test_stale_running_run_reconciles_only_durable_success_usage(monkeypatch):
    run = _run(started_seconds_ago=run_recovery.STALE_RUN_RECOVERY_SECONDS + 1)
    successful = SimpleNamespace(
        status="success",
        prompt_tokens=100,
        completion_tokens=25,
        cost_usd=1.25,
        raw_meta={},
    )
    unknown = SimpleNamespace(
        status="in_flight",
        prompt_tokens=900,
        completion_tokens=900,
        cost_usd=9.99,
        raw_meta={"logical_run_id": str(run.id)},
    )
    db = _Db(locked_run=run, provider_calls=[successful, unknown])

    async def _audit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(run_recovery.audit_service, "record", _audit)

    assert await run_recovery.recover_stale_run_execution(db, run=run) is True
    assert run.status == "failed"
    assert run.total_tokens == 125
    assert float(run.total_cost_usd) == pytest.approx(1.25)
    assert unknown.status == "unknown"


@pytest.mark.asyncio
async def test_stale_running_run_without_provider_call_still_fails_closed(monkeypatch):
    run = _run(started_seconds_ago=run_recovery.STALE_RUN_RECOVERY_SECONDS + 1)
    db = _Db(locked_run=run, provider_calls=[])

    async def _audit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(run_recovery.audit_service, "record", _audit)

    assert await run_recovery.recover_stale_run_execution(db, run=run) is True
    assert run.status == "failed"
    assert run.completed_at is not None
    assert "replay was intentionally blocked" in run.error_message
