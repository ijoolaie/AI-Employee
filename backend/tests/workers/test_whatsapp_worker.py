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
async def test_whatsapp_worker_rejects_cross_tenant_governance_binding_before_lookup():
    row_tenant_id, proof_tenant_id, run_id = uuid4(), uuid4(), uuid4()
    row = SimpleNamespace(
        tenant_id=row_tenant_id,
        payload={
            "run_id": str(run_id),
            "approval_request_id": str(uuid4()),
            "channel_id": str(uuid4()),
            "tool_name": "whatsapp.send_text",
            "tool_call_id": "call_cross_tenant",
            "recipient": "+15551234567",
            "text": "must not cross tenant boundary",
            "_agent_governance": {
                "tenant_id": str(proof_tenant_id),
                "agent_instance_id": str(uuid4()),
                "run_id": str(run_id),
                "tool_name": "whatsapp.send_text",
            },
        },
    )

    class _NoLookupDB:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            return _Result(None)

    db = _NoLookupDB()
    with pytest.raises(ValidationAppError, match="governance binding mismatch"):
        await whatsapp_worker._validate_and_load(db, row)

    assert db.statements == []

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
@pytest.mark.parametrize("tampered_field", ["channel_id", "recipient", "text"])
async def test_whatsapp_worker_rejects_approval_payload_mismatch(tampered_field):
    tenant_id, agent_id, run_id = uuid4(), uuid4(), uuid4()
    approval_id, channel_id = uuid4(), uuid4()
    tool_call_id = "call_exact_binding"
    approved_arguments = {
        "channel_id": str(channel_id),
        "recipient": "+15551234567",
        "text": "original approved message",
    }
    payload = {
        **approved_arguments,
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
    }
    payload[tampered_field] = {
        "channel_id": str(uuid4()),
        "recipient": "+15557654321",
        "text": "message changed after approval",
    }[tampered_field]
    row = SimpleNamespace(
        id=uuid4(), kind="whatsapp.send_text", tenant_id=tenant_id,
        status="processing", attempts=1, payload=payload,
    )
    approval = SimpleNamespace(
        id=approval_id, tenant_id=tenant_id, run_id=run_id,
        tool_name="whatsapp.send_text", tool_call_id=tool_call_id,
        status="consumed", arguments=approved_arguments,
    )

    class _ApprovalDB:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            return _Result(approval)

    db = _ApprovalDB()
    with pytest.raises(ValidationAppError, match="does not match its consumed exact-call approval"):
        await whatsapp_worker._validate_and_load(db, row)

    # Reject before loading a channel or reaching policy/provider execution.
    assert len(db.statements) == 1


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

@pytest.mark.asyncio
async def test_whatsapp_worker_rejects_channel_owned_by_another_tenant():
    tenant_id = uuid4()
    agent_id, run_id, approval_id, channel_id = uuid4(), uuid4(), uuid4(), uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=tenant_id,
        status="processing",
        attempts=1,
        payload={
            "channel_id": str(channel_id),
            "recipient": "+15551234567",
            "text": "tenant-scoped message",
            "run_id": str(run_id),
            "tool_name": "whatsapp.send_text",
            "tool_call_id": "call_tenant_scoped",
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
        tool_call_id="call_tenant_scoped",
        status="consumed",
        arguments={
            "channel_id": str(channel_id),
            "recipient": row.payload["recipient"],
            "text": row.payload["text"],
        },
    )

    class _TenantScopedDB:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            return _Result(approval if len(self.statements) == 1 else None)

    db = _TenantScopedDB()
    with pytest.raises(ValidationAppError, match="Active WhatsApp channel not found for this tenant"):
        await whatsapp_worker._validate_and_load(db, row)

    assert len(db.statements) == 2
    channel_query = str(db.statements[1])
    assert "customer_channels.tenant_id" in channel_query
    assert tenant_id in db.statements[1].compile().params.values()


@pytest.mark.asyncio
async def test_whatsapp_worker_keeps_two_tenant_content_isolated_at_provider_boundary(monkeypatch):
    tenants = [
        {
            "tenant_id": uuid4(),
            "channel_id": uuid4(),
            "recipient": "+15550000001",
            "text": "private tenant alpha incident 7f31",
            "channel_marker": "alpha-channel-config",
        },
        {
            "tenant_id": uuid4(),
            "channel_id": uuid4(),
            "recipient": "+15550000002",
            "text": "private tenant beta incident 9c42",
            "channel_marker": "beta-channel-config",
        },
    ]
    rows = [
        SimpleNamespace(
            id=uuid4(),
            kind="whatsapp.send_text",
            tenant_id=item["tenant_id"],
            status="processing",
            attempts=1,
            payload={"recipient": item["recipient"], "text": item["text"]},
        )
        for item in tenants
    ]
    databases = [_DB(row) for row in rows]
    contexts = iter(databases)
    channels = [
        SimpleNamespace(
            id=item["channel_id"],
            channel_type="whatsapp",
            config={"channel_marker": item["channel_marker"]},
        )
        for item in tenants
    ]
    validations = {
        row.id: (item["tenant_id"], channel, row.payload, SimpleNamespace(), uuid4(), uuid4(), None)
        for item, row, channel in zip(tenants, rows, channels, strict=True)
    }
    provider = AsyncMock(
        side_effect=[
            SimpleNamespace(provider_message_id="provider-alpha", status="sent"),
            SimpleNamespace(provider_message_id="provider-beta", status="sent"),
        ]
    )

    async def mark_dispatched(_db, row):
        row.status = "dispatched"

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(next(contexts)))

    async def validate(_db, row):
        return validations[row.id]

    monkeypatch.setattr(whatsapp_worker, "_validate_and_load", validate)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)
    monkeypatch.setattr(whatsapp_worker, "mark_dispatched", mark_dispatched)

    for row in rows:
        await whatsapp_worker._send(str(row.id))

    assert provider.await_count == 2
    for index, (item, row, call) in enumerate(zip(tenants, rows, provider.await_args_list, strict=True)):
        arguments = call.kwargs
        assert arguments["tenant_id"] == item["tenant_id"]
        assert arguments["channel_type"] == "whatsapp"
        assert arguments["channel_config"] == {"channel_marker": item["channel_marker"]}
        assert arguments["recipient"] == item["recipient"]
        assert arguments["text"] == item["text"]
        other = tenants[1 - index]
        assert other["recipient"] not in repr(arguments)
        assert other["text"] not in repr(arguments)
        assert other["channel_marker"] not in repr(arguments)
        assert row.status == "dispatched"
        assert databases[index].events.count("commit") == 2
        assert databases[index].events.count("rollback") == 0



@pytest.mark.asyncio
async def test_agent_whatsapp_direct_and_nested_tenant_content_isolated_at_provider(monkeypatch):
    tenants = [
        {
            "hierarchy": "direct_vendor_customer",
            "tenant_id": uuid4(),
            "agent_instance_id": uuid4(),
            "run_id": uuid4(),
            "delegation_id": uuid4(),
            "approval_id": uuid4(),
            "channel_id": uuid4(),
            "tool_call_id": "direct-call-01",
            "recipient": "+15550000101",
            "text": "DIRECT-CUSTOMER-ONLY incident marker",
            "channel_marker": "direct-customer-channel",
        },
        {
            "hierarchy": "reseller_customer",
            "tenant_id": uuid4(),
            "agent_instance_id": uuid4(),
            "run_id": uuid4(),
            "delegation_id": uuid4(),
            "approval_id": uuid4(),
            "channel_id": uuid4(),
            "tool_call_id": "nested-call-02",
            "recipient": "+15550000202",
            "text": "RESELLER-CUSTOMER-ONLY incident marker",
            "channel_marker": "reseller-customer-channel",
        },
    ]
    rows = []
    approvals = []
    channels = []
    for item in tenants:
        row = SimpleNamespace(
            id=uuid4(),
            kind="whatsapp.send_text",
            tenant_id=item["tenant_id"],
            status="processing",
            attempts=1,
            last_error=None,
            dead_at=None,
            payload={
                "run_id": str(item["run_id"]),
                "approval_request_id": str(item["approval_id"]),
                "channel_id": str(item["channel_id"]),
                "tool_name": "whatsapp.send_text",
                "tool_call_id": item["tool_call_id"],
                "recipient": item["recipient"],
                "text": item["text"],
                "_agent_governance": {
                    "tenant_id": str(item["tenant_id"]),
                    "agent_instance_id": str(item["agent_instance_id"]),
                    "run_id": str(item["run_id"]),
                    "tool_name": "whatsapp.send_text",
                    "delegation_id": str(item["delegation_id"]),
                },
            },
        )
        rows.append(row)
        approvals.append(
            SimpleNamespace(
                id=item["approval_id"],
                tenant_id=item["tenant_id"],
                run_id=item["run_id"],
                tool_name="whatsapp.send_text",
                tool_call_id=item["tool_call_id"],
                status="consumed",
                arguments={
                    "channel_id": str(item["channel_id"]),
                    "recipient": item["recipient"],
                    "text": item["text"],
                },
            )
        )
        channels.append(
            SimpleNamespace(
                id=item["channel_id"],
                tenant_id=item["tenant_id"],
                channel_type="whatsapp",
                is_active=True,
                config={"channel_marker": item["channel_marker"]},
            )
        )

    class _GovernedDB(_DB):
        def __init__(self, row, approval, channel):
            super().__init__(row)
            self.approval = approval
            self.channel = channel
            self.query_index = 0

        async def execute(self, *_args, **_kwargs):
            if self.query_index == 0:
                result = self.row
            elif self.query_index % 2 == 1:
                result = self.approval
            else:
                result = self.channel
            self.query_index += 1
            return _Result(result)

    databases = [
        _GovernedDB(row, approval, channel)
        for row, approval, channel in zip(rows, approvals, channels, strict=True)
    ]
    contexts = iter(databases)
    deliveries = AsyncMock(
        side_effect=[
            SimpleNamespace(provider_message_id="direct-provider-message", status="sent"),
            SimpleNamespace(provider_message_id="nested-provider-message", status="sent"),
        ]
    )
    authorization_requests = []
    expected_by_delegation = {
        item["delegation_id"]: item for item in tenants
    }

    async def authorize(_db, request):
        authorization_requests.append(request)
        expected = expected_by_delegation[request.delegation_id]
        assert request.tenant_id == expected["tenant_id"]
        assert request.agent_instance_id == expected["agent_instance_id"]
        assert request.run_id == expected["run_id"]
        assert request.action == "tool.execute"
        assert request.tool_name == "whatsapp.send_text"
        assert request.required_permission == "run.execute"

    async def mark_dispatched(_db, row):
        row.status = "dispatched"

    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(next(contexts)))
    monkeypatch.setattr(whatsapp_worker, "assert_authorized", authorize)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", deliveries)
    monkeypatch.setattr(whatsapp_worker, "mark_dispatched", mark_dispatched)

    for row in rows:
        await whatsapp_worker._send(str(row.id))

    assert deliveries.await_count == 2
    assert len(authorization_requests) == 4
    for index, (item, row, call, db) in enumerate(
        zip(tenants, rows, deliveries.await_args_list, databases, strict=True)
    ):
        arguments = call.kwargs
        assert arguments["tenant_id"] == item["tenant_id"]
        assert arguments["channel_type"] == "whatsapp"
        assert arguments["channel_config"] == {"channel_marker": item["channel_marker"]}
        assert arguments["recipient"] == item["recipient"]
        assert arguments["text"] == item["text"]
        other = tenants[1 - index]
        assert other["recipient"] not in repr(arguments)
        assert other["text"] not in repr(arguments)
        assert other["channel_marker"] not in repr(arguments)
        assert row.status == "dispatched"
        assert db.query_index == 5
        assert db.events.count("commit") == 2
        assert db.events.count("rollback") == 0
        matching_authorizations = [
            request for request in authorization_requests
            if request.run_id == item["run_id"]
        ]
        assert len(matching_authorizations) == 2



@pytest.mark.asyncio
@pytest.mark.parametrize("hierarchy", ["direct_vendor_customer", "reseller_customer"])
async def test_agent_whatsapp_revoked_delegation_dead_letters_after_retry_exhaustion(monkeypatch, hierarchy):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from app.core import config
    from app.core.exceptions import ValidationAppError

    tenant_id, agent_id, run_id, delegation_id = uuid4(), uuid4(), uuid4(), uuid4()
    approval_id, channel_id = uuid4(), uuid4()
    recipient = "+15550000303"
    text = f"{hierarchy} must never be sent"
    tool_call_id = f"{hierarchy}-approval"
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        tenant_id=tenant_id,
        status="processing",
        attempts=1,
        payload={
            "run_id": str(run_id),
            "approval_request_id": str(approval_id),
            "channel_id": str(channel_id),
            "tool_name": "whatsapp.send_text",
            "tool_call_id": tool_call_id,
            "recipient": recipient,
            "text": text,
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(agent_id),
                "run_id": str(run_id),
                "tool_name": "whatsapp.send_text",
                "delegation_id": str(delegation_id),
            },
        },
        last_error=None,
        dead_at=None,
        available_at=None,
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
            "recipient": recipient,
            "text": text,
        },
    )
    channel = SimpleNamespace(
        id=channel_id,
        tenant_id=tenant_id,
        channel_type="whatsapp",
        is_active=True,
        config={"channel_marker": hierarchy},
    )

    class _RetryDB:
        def __init__(self):
            self.rows = [row, approval, channel, row]
            self.events = []

        async def execute(self, *_args, **_kwargs):
            return _Result(self.rows.pop(0))

        async def commit(self):
            self.events.append("commit")

        async def rollback(self):
            self.events.append("rollback")

        async def flush(self):
            self.events.append("flush")

    db = _RetryDB()
    authorization_requests = []
    provider = AsyncMock()

    async def revoked(_db, request):
        authorization_requests.append(request)
        assert request.tenant_id == tenant_id
        assert request.agent_instance_id == agent_id
        assert request.run_id == run_id
        assert request.delegation_id == delegation_id
        assert request.tool_name == "whatsapp.send_text"
        raise ValidationAppError(f"{hierarchy} delegated grant revoked before WhatsApp")

    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(outbox_max_attempts=1))
    monkeypatch.setattr(whatsapp_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(whatsapp_worker, "assert_authorized", revoked)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", provider)

    await whatsapp_worker._send(str(row.id))

    assert len(authorization_requests) == 1
    provider.assert_not_awaited()
    assert row.status == "dead"
    assert row.dead_at is not None
    assert isinstance(row.dead_at, datetime)
    assert row.dead_at.tzinfo == timezone.utc
    assert hierarchy in row.last_error
    assert db.events.count("rollback") == 1
    assert db.events.count("flush") == 1
    assert db.events.count("commit") == 1
