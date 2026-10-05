from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.workers import outbox_worker


class _Span:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, *_args):
        return None


class _DB:
    def __init__(self, events):
        self.events = events
        self.row = None

    async def commit(self):
        self.events.append("commit")

    async def rollback(self):
        self.events.append("rollback")

    async def get(self, *_args):
        return self.row


@asynccontextmanager
async def _session(db):
    yield db


@pytest.mark.asyncio
async def test_non_email_outbox_commits_processing_claim_before_broker_publish(monkeypatch):
    events = []
    db = _DB(events)
    row = SimpleNamespace(
        id=uuid4(),
        kind="workflow.execute",
        tenant_id=uuid4(),
        payload={"workflow_run_id": str(uuid4())},
        attempts=1,
        status="processing",
    )
    db.row = row

    async def fake_claim(_db, *, limit):
        return [row]

    async def fake_mark_dispatched(_db, _row):
        events.append("mark_dispatched")

    class _Task:
        @staticmethod
        def delay(*_args):
            events.append("publish")

    fake_workflow_module = SimpleNamespace(execute_workflow_task=_Task)

    monkeypatch.setattr(outbox_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(outbox_worker.outbox_service, "claim", fake_claim)
    monkeypatch.setattr(outbox_worker.outbox_service, "mark_dispatched", fake_mark_dispatched)
    monkeypatch.setattr(outbox_worker, "span", lambda *args, **kwargs: _Span())
    monkeypatch.setitem(sys.modules, "app.workers.workflow_worker", fake_workflow_module)

    assert await outbox_worker._dispatch_async(limit=1) == 1
    assert events.index("commit") < events.index("publish")
    assert events.index("publish") < events.index("mark_dispatched")
    assert events.count("commit") == 2


@pytest.mark.asyncio
async def test_broker_publish_failure_retries_after_durable_claim(monkeypatch):
    events = []
    db = _DB(events)
    row = SimpleNamespace(
        id=uuid4(),
        kind="workflow.execute",
        tenant_id=uuid4(),
        payload={"workflow_run_id": str(uuid4())},
        attempts=1,
        status="processing",
    )
    db.row = row

    async def fake_claim(_db, *, limit):
        return [row]

    async def fake_mark_retry(_db, _row, _error, delay_seconds):
        events.append("mark_retry")

    class _Task:
        @staticmethod
        def delay(*_args):
            events.append("publish")
            raise RuntimeError("broker unavailable")

    fake_workflow_module = SimpleNamespace(execute_workflow_task=_Task)

    monkeypatch.setattr(outbox_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(outbox_worker.outbox_service, "claim", fake_claim)
    monkeypatch.setattr(outbox_worker.outbox_service, "mark_retry", fake_mark_retry)
    monkeypatch.setattr(outbox_worker, "span", lambda *args, **kwargs: _Span())
    monkeypatch.setitem(sys.modules, "app.workers.workflow_worker", fake_workflow_module)

    assert await outbox_worker._dispatch_async(limit=1) == 0
    assert events.index("commit") < events.index("publish")
    assert events.index("rollback") < events.index("mark_retry")
