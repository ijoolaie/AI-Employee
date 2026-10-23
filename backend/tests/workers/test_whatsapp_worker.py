from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.workers import whatsapp_worker


class _Result:
    def __init__(self, row):
        self.row = row

    def scalar_one_or_none(self):
        return self.row


class _DB:
    def __init__(self, row):
        self.row = row
        self.events = []

    async def execute(self, *_args, **_kwargs):
        return _Result(self.row)

    async def commit(self):
        self.events.append("commit")

    async def rollback(self):
        self.events.append("rollback")


@asynccontextmanager
async def _session(db):
    yield db


@pytest.mark.asyncio
async def test_whatsapp_worker_rejects_missing_governance_proof_before_provider(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=uuid4(),
        status="processing",
        attempts=1,
        payload={"channel_id": str(uuid4()), "recipient": "+15551234567", "text": "no proof"},
    )
    db = _DB(row)
    provider = AsyncMock()
    retries = AsyncMock(side_effect=lambda _db, message, *_args, **_kwargs: setattr(message, "status", "pending"))

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)
    monkeypatch.setattr(whatsapp_worker, "mark_retry", retries)

    await whatsapp_worker._send(str(row.id))

    provider.assert_not_awaited()
    retries.assert_awaited_once()
    assert row.status == "pending"


@pytest.mark.asyncio
async def test_whatsapp_worker_never_retries_after_provider_boundary(monkeypatch):
    tenant_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=tenant_id,
        status="processing",
        attempts=1,
        payload={"channel_id": str(uuid4()), "recipient": "+15551234567", "text": "approved"},
        last_error=None,
    )
    db = _DB(row)
    channel = SimpleNamespace(id=uuid4(), channel_type="whatsapp", config={})
    approval = SimpleNamespace(id=uuid4())
    agent_id, run_id = uuid4(), uuid4()
    payload = row.payload
    provider = AsyncMock(side_effect=TimeoutError("provider response timed out"))
    retries = AsyncMock()

    async def validated(_db, _row):
        return tenant_id, channel, payload, approval, agent_id, run_id, None

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "_validate_and_load", validated)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)
    monkeypatch.setattr(whatsapp_worker, "mark_retry", retries)

    await whatsapp_worker._send(str(row.id))

    provider.assert_awaited_once()
    retries.assert_not_awaited()
    assert row.status == "uncertain"
    assert "TimeoutError" in row.last_error
    assert db.events.count("commit") == 2
