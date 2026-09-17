from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services import trace_service


class _Result:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._rows))


class _Db:
    def __init__(self, run, calls, audits):
        self.run = run
        self.calls = calls
        self.audits = audits
        self.index = 0

    async def execute(self, _statement):
        self.index += 1
        if self.index == 1:
            return _Result(scalar=self.run)
        if self.index == 2:
            return _Result(rows=self.calls)
        if self.index == 3:
            return _Result(rows=self.audits)
        raise AssertionError("unexpected database query")


@pytest.mark.asyncio
async def test_get_run_trace_is_tenant_scoped_and_merges_durable_events():
    run_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=run_id,
        tenant_id=tenant_id,
        status="success",
        started_at=now,
        completed_at=now,
        total_tokens=125,
        total_cost_usd=1.25,
    )
    call = SimpleNamespace(
        created_at=now,
        provider="lm_studio",
        model="google/gemma-4e4b",
        status="success",
        prompt_tokens=100,
        completion_tokens=25,
        cost_usd=1.25,
        latency_ms=42,
        prompt_version="v1",
        request_id="req-1",
        raw_meta={"logical_turn": "1"},
        error_message=None,
    )
    audit = SimpleNamespace(
        created_at=now,
        action="run.created",
        status="success",
        request_id="req-0",
        metadata_={"source": "api"},
    )

    db = _Db(run, [call], [audit])
    trace = await trace_service.get_run_trace(db, run_id=run_id, tenant_id=tenant_id)

    assert trace["run_id"] == run_id
    assert trace["status"] == "success"
    assert trace["total_tokens"] == 125
    assert trace["total_cost_usd"] == pytest.approx(1.25)
    assert [event["type"] for event in trace["events"]] == ["audit", "ai_provider_call"]
    assert trace["events"][0]["action"] == "run.created"
    assert trace["events"][1]["provider"] == "lm_studio"
    assert trace["events"][1]["request_id"] == "req-1"
    assert trace["events"][1]["metadata"]["logical_turn"] == "1"
    assert db.index == 3


@pytest.mark.asyncio
async def test_get_run_trace_rejects_cross_tenant_run():
    run_id = uuid4()
    requested_tenant_id = uuid4()
    run = None
    db = _Db(run, [], [])

    with pytest.raises(NotFoundError):
        await trace_service.get_run_trace(
            db, run_id=run_id, tenant_id=requested_tenant_id
        )

    assert db.index == 1
