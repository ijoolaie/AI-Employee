from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.workers import whatsapp_worker


@pytest.fixture(autouse=True)
def _allow_active_tenant_in_worker_unit_tests(monkeypatch):
    async def assert_active(_db, *, tenant_id):
        return SimpleNamespace(id=tenant_id, status="active")

    monkeypatch.setattr(
        "app.services.billing_service.assert_outbound_delivery_entitlement",
        assert_active,
    )



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



@pytest.mark.asyncio
async def test_whatsapp_worker_rejects_approval_for_different_message():
    tenant_id, agent_id, run_id = uuid4(), uuid4(), uuid4()
    approval_id, channel_id = uuid4(), uuid4()
    tool_call_id = "call_exact_binding"
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=tenant_id,
        status="processing",
        attempts=1,
        payload={
            "channel_id": str(channel_id),
            "recipient": "+15551234567",
            "text": "message changed after approval",
            "run_id": str(run_id),
            "tool_name": "whatsapp.send_text",
            "tool_call_id": tool_call_id,
            "approval_request_id": str(approval_id),
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(agent_id),
                "run_id": str(run_id),
                "tool_name": "whatsapp.send_text",
            },
        },
    )
    approval = SimpleNamespace(
        id=approval_id,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="whatsapp.send_text",
        tool_call_id=tool_call_id,
        status="consumed",
        arguments={
            "channel_id": str(channel_id),
            "recipient": "+15551234567",
            "text": "original approved message",
        },
    )

    class _ApprovalDB:
        async def execute(self, *_args, **_kwargs):
            return _Result(approval)

    with pytest.raises(ValidationAppError, match="does not match its consumed exact-call approval"):
        await whatsapp_worker._validate_and_load(_ApprovalDB(), row)


@pytest.mark.asyncio
async def test_whatsapp_worker_dead_letters_when_commercial_entitlement_is_inactive(monkeypatch):
    from app.core.exceptions import TenantInactiveError

    tenant_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(), kind="whatsapp.send_text", tenant_id=tenant_id,
        status="processing", attempts=1, payload={}, last_error=None, dead_at=None,
    )
    db = _DB(row)
    provider = AsyncMock()
    retries = AsyncMock()

    async def validated(_db, _row):
        return tenant_id, SimpleNamespace(id=uuid4(), channel_type="whatsapp", config={}), {}, None, uuid4(), uuid4(), None

    async def denied(_db, *, tenant_id):
        raise TenantInactiveError("commercial entitlement expired")

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "_validate_and_load", validated)
    monkeypatch.setattr("app.services.billing_service.assert_outbound_delivery_entitlement", denied)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)
    monkeypatch.setattr(whatsapp_worker, "mark_retry", retries)

    await whatsapp_worker._send(str(row.id))

    provider.assert_not_awaited()
    retries.assert_not_awaited()
    assert row.status == "dead"
    assert row.dead_at is not None
    assert "commercial entitlement expired" in row.last_error


@pytest.mark.asyncio
async def test_whatsapp_delegation_revoked_after_uncertain_commit_blocks_provider(monkeypatch):
    tenant_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=tenant_id,
        status="processing",
        attempts=1,
        payload={"recipient": "+15551234567", "text": "must not send after revocation"},
        last_error=None,
    )
    db = _DB(row)
    channel = SimpleNamespace(id=uuid4(), channel_type="whatsapp", config={})
    approval = SimpleNamespace(id=uuid4())
    agent_id, run_id = uuid4(), uuid4()
    provider = AsyncMock()
    retries = AsyncMock()
    validation_calls = 0

    async def validate(_db, _row):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 2:
            raise ValidationAppError("delegated authority revoked before WhatsApp provider")
        return tenant_id, channel, row.payload, approval, agent_id, run_id, uuid4()

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "_validate_and_load", validate)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)
    monkeypatch.setattr(whatsapp_worker, "mark_retry", retries)

    await whatsapp_worker._send(str(row.id))

    assert validation_calls == 2
    provider.assert_not_awaited()
    retries.assert_not_awaited()
    assert row.status == "uncertain"
    assert "delegated authority revoked before WhatsApp provider" in row.last_error
    assert db.events.count("commit") == 2
    assert db.events.count("rollback") == 1

@pytest.mark.asyncio
async def test_whatsapp_pre_provider_retry_exhaustion_dead_letters_without_provider(monkeypatch):
    from datetime import datetime, timezone

    from app.core import config

    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=uuid4(),
        status="processing",
        attempts=1,
        payload={"channel_id": str(uuid4()), "recipient": "+15551234567", "text": "missing proof"},
        last_error=None,
        dead_at=None,
        available_at=None,
    )
    db = _DB(row)
    db.flush = AsyncMock()
    provider = AsyncMock()

    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(outbox_max_attempts=1))
    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)

    await whatsapp_worker._send(str(row.id))

    provider.assert_not_awaited()
    assert row.status == "dead"
    assert row.dead_at is not None
    assert isinstance(row.dead_at, datetime)
    assert row.dead_at.tzinfo == timezone.utc
    assert "missing Agent governance proof" in row.last_error
    assert db.events.count("rollback") == 1
    assert db.events.count("commit") == 1
