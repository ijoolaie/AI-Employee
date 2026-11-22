from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import outbox_service
from app.workers import email_worker
from app.workers.email_worker import _build_email


@pytest.fixture(autouse=True)
def _allow_active_tenant_in_worker_unit_tests(monkeypatch):
    async def assert_active(_db, *, tenant_id):
        return SimpleNamespace(id=tenant_id, status="active")

    monkeypatch.setattr(
        "app.services.billing_service.assert_outbound_delivery_entitlement",
        assert_active,
    )



class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        if not self._rows:
            return None
        if len(self._rows) > 1:
            raise AssertionError("expected at most one row")
        return self._rows[0]


class _DB:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None
        self.commits = 0

    async def execute(self, statement):
        self.statement = statement
        return _Result(self.rows)

    async def flush(self):
        return None

    async def commit(self):
        self.commits += 1


class _Settings:
    smtp_from_email = "noreply@example.test"
    smtp_host = "smtp.example.test"
    smtp_port = 25
    smtp_use_starttls = False
    smtp_username = None
    smtp_password = None


class _DBContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _SMTP:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def send_message(self, msg):
        raise RuntimeError("connection lost after provider acceptance")


def test_email_message_id_is_stable_for_outbox_item():
    payload = {"to": ["user@example.test"], "subject": "Hello", "body": "Body"}
    outbox_id = str(uuid4())

    first = _build_email(payload, outbox_id, _Settings())
    second = _build_email(payload, outbox_id, _Settings())

    assert first["Message-ID"] == second["Message-ID"]
    assert outbox_id in first["Message-ID"]


@pytest.mark.asyncio
async def test_claim_includes_stale_email_delivery_in_recovery_predicate():
    db = _DB([])

    rows = await outbox_service.claim(db)

    predicate = db.statement.whereclause.compile(compile_kwargs={"literal_binds": True})
    sql = str(predicate)
    assert "email.send" in sql
    assert rows == []


@pytest.mark.asyncio
async def test_email_worker_ignores_non_email_outbox_rows_before_smtp(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
        kind="whatsapp.send_text",
        status="processing",
        attempts=1,
        payload={"to": ["private@example.test"], "subject": "Wrong route", "body": "must not send"},
        tenant_id=uuid4(),
        last_error=None,
    )
    db = _DB([row])
    smtp_attempts = []

    class _UnexpectedSMTP:
        def __init__(self, *args, **kwargs):
            smtp_attempts.append((args, kwargs))
            raise AssertionError("non-email outbox rows must not reach SMTP")

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _UnexpectedSMTP)

    await email_worker._send(str(row.id))

    assert smtp_attempts == []
    assert row.status == "processing"
    assert db.commits == 0


@pytest.mark.asyncio
async def test_email_delivery_select_serializes_concurrent_workers(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        payload={"to": ["user@example.test"], "subject": "Hello", "body": "Body"},
        tenant_id=None,
        last_error=None,
    )
    db = _DB([row])

    async def authorize(*args, **kwargs):
        return None

    async def mark_dispatched(*args, **kwargs):
        raise AssertionError("SMTP should not be reached by this structural test")

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker, "smtplib", SimpleNamespace())
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    class _ExpectedSMTPFailure:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("test stop before SMTP")

    email_worker.smtplib.SMTP = _ExpectedSMTPFailure
    await email_worker._send(str(row.id))

    assert db.statement._for_update_arg is not None
    assert row.status == "uncertain"
    assert db.commits >= 2


@pytest.mark.asyncio
async def test_governed_email_revalidates_after_uncertain_commit(monkeypatch):
    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    delegation_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        payload={
            "to": ["user@example.test"],
            "subject": "Hello",
            "body": "Body",
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(agent_instance_id),
                "run_id": str(run_id),
                "tool_name": "email.send",
                "delegation_id": str(delegation_id),
            },
        },
        tenant_id=tenant_id,
        last_error=None,
    )
    db = _DB([row])
    authorization_calls = 0

    async def authorize(*args, **kwargs):
        nonlocal authorization_calls
        authorization_calls += 1

    async def mark_dispatched(*args, **kwargs):
        row.status = "dispatched"

    class _AcceptedSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, msg):
            return None

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _AcceptedSMTP)
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    await email_worker._send(str(row.id))

    assert authorization_calls == 2
    assert row.status == "dispatched"
    assert db.commits >= 2


@pytest.mark.asyncio
async def test_email_side_effect_failure_remains_uncertain(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        payload={"to": ["user@example.test"], "subject": "Hello", "body": "Body"},
        tenant_id=None,
        last_error=None,
    )
    db = _DB([row])

    async def commit():
        db.commits += 1

    db.commit = commit

    async def authorize(*args, **kwargs):
        return None

    async def fail_retry(*args, **kwargs):
        raise AssertionError("uncertain SMTP outcome must not be retried")

    metric_events = []

    class _Metric:
        def labels(self, outcome):
            return SimpleNamespace(inc=lambda: metric_events.append(outcome))

    monkeypatch.setattr(email_worker, "OUTBOX_EMAIL_DELIVERY", _Metric())
    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _SMTP)
    monkeypatch.setattr(outbox_service, "mark_retry", fail_retry)

    await email_worker._send(str(row.id))

    assert row.status == "uncertain"
    assert "provider acceptance" in row.last_error
    assert metric_events == ["uncertain"]
    assert db.commits >= 2


@pytest.mark.asyncio
async def test_customer_handoff_email_worker_invokes_configured_destination(monkeypatch):
    tenant_id = uuid4()
    conversation_id = uuid4()
    channel_id = uuid4()
    recipient = "ops@example.test"
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        tenant_id=tenant_id,
        last_error=None,
        payload={
            "to": [recipient],
            "subject": "Customer requested human support",
            "body": (
                f"tenant_id={tenant_id}\\n"
                f"conversation_id={conversation_id}\\n"
                f"channel_id={channel_id}\\n"
            ),
        },
    )
    db = _DB([row])
    delivered = []
    metric_events = []

    class _Metric:
        def labels(self, outcome):
            return SimpleNamespace(inc=lambda: metric_events.append(outcome))

    async def authorize(*args, **kwargs):
        return None

    async def mark_dispatched(db_arg, row_arg):
        row_arg.status = "dispatched"

    class _CapturingSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, msg):
            delivered.append(msg)

    monkeypatch.setattr(email_worker, "OUTBOX_EMAIL_DELIVERY", _Metric())
    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _CapturingSMTP)
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    await email_worker._send(str(row.id))

    assert len(delivered) == 1
    assert delivered[0]["To"] == recipient
    assert delivered[0]["Subject"] == "Customer requested human support"
    body = delivered[0].get_content()
    assert str(tenant_id) in body
    assert str(conversation_id) in body
    assert str(channel_id) in body
    assert row.status == "dispatched"
    assert metric_events == ["success"]


@pytest.mark.asyncio
async def test_email_worker_keeps_two_tenant_handoff_content_isolated_at_smtp(monkeypatch):
    tenants = [
        {
            "tenant_id": uuid4(),
            "conversation_id": uuid4(),
            "channel_id": uuid4(),
            "recipient": "tenant-a-ops@example.test",
        },
        {
            "tenant_id": uuid4(),
            "conversation_id": uuid4(),
            "channel_id": uuid4(),
            "recipient": "tenant-b-ops@example.test",
        },
    ]
    rows = [
        SimpleNamespace(
            id=uuid4(),
            kind="email.send",
            status="processing",
            attempts=1,
            tenant_id=item["tenant_id"],
            last_error=None,
            payload={
                "to": [item["recipient"]],
                "subject": "Customer requested human support",
                "body": (
                    f"tenant_id={item['tenant_id']}\n"
                    f"conversation_id={item['conversation_id']}\n"
                    f"channel_id={item['channel_id']}\n"
                ),
            },
        )
        for item in tenants
    ]
    databases = [_DB([row]) for row in rows]
    contexts = iter(databases)
    delivered = []

    class _CapturingSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, msg):
            delivered.append(msg)

    async def authorize(*args, **kwargs):
        return None

    async def mark_dispatched(_db, row):
        row.status = "dispatched"

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(next(contexts)))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _CapturingSMTP)
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    for row in rows:
        await email_worker._send(str(row.id))

    assert len(delivered) == 2
    for index, (item, row, message) in enumerate(zip(tenants, rows, delivered, strict=True)):
        body = message.get_content()
        assert message["To"] == item["recipient"]
        assert message["Subject"] == "Customer requested human support"
        assert str(item["tenant_id"]) in body
        assert str(item["conversation_id"]) in body
        assert str(item["channel_id"]) in body
        other = tenants[1 - index]
        assert other["recipient"] not in body
        assert str(other["tenant_id"]) not in body
        assert str(other["conversation_id"]) not in body
        assert str(other["channel_id"]) not in body
        assert row.status == "dispatched"


@pytest.mark.asyncio
async def test_email_success_metric_is_not_emitted_when_final_commit_fails(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        payload={"to": ["user@example.test"], "subject": "Hello", "body": "Body"},
        tenant_id=None,
        last_error=None,
    )

    class _FailFinalCommitDB(_DB):
        async def commit(self):
            self.commits += 1
            if self.commits == 2:
                raise RuntimeError("simulated final commit failure")

    db = _FailFinalCommitDB([row])
    metric_events = []

    class _Metric:
        def labels(self, outcome):
            return SimpleNamespace(inc=lambda: metric_events.append(outcome))

    async def authorize(*args, **kwargs):
        return None

    async def mark_dispatched(db_arg, row_arg):
        row_arg.status = "dispatched"

    class _AcceptedSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, msg):
            return None

    monkeypatch.setattr(email_worker, "OUTBOX_EMAIL_DELIVERY", _Metric())
    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _AcceptedSMTP)
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    with pytest.raises(RuntimeError, match="simulated final commit failure"):
        await email_worker._send(str(row.id))

    assert metric_events == []
    assert db.commits == 2



@pytest.mark.asyncio
async def test_governed_email_rejects_cross_tenant_row_binding_before_smtp(monkeypatch):
    row_tenant_id = uuid4()
    proof_tenant_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        tenant_id=row_tenant_id,
        last_error=None,
        payload={
            "to": ["private@example.test"],
            "subject": "Tenant-bound message",
            "body": "must not send",
            "_agent_governance": {
                "tenant_id": str(proof_tenant_id),
                "agent_instance_id": str(uuid4()),
                "run_id": str(uuid4()),
                "tool_name": "email.send",
            },
        },
    )
    db = _DB([row])
    authorization = AsyncMock()
    smtp_attempts = []

    class _UnexpectedSMTP:
        def __init__(self, *args, **kwargs):
            smtp_attempts.append((args, kwargs))
            raise AssertionError("cross-tenant email must be rejected before SMTP")

    async def mark_retry(_db, message, *_args, **_kwargs):
        message.status = "pending"

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorization)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _UnexpectedSMTP)
    monkeypatch.setattr(outbox_service, "mark_retry", mark_retry)

    await email_worker._send(str(row.id))

    authorization.assert_not_awaited()
    assert smtp_attempts == []
    assert row.status == "pending"


@pytest.mark.asyncio
async def test_governed_email_revocation_after_uncertain_commit_blocks_smtp(monkeypatch):
    tenant_id = uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        tenant_id=tenant_id,
        last_error=None,
        payload={
            "to": ["private@example.test"],
            "subject": "Tenant-bound message",
            "body": "must not send after revocation",
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(uuid4()),
                "run_id": str(uuid4()),
                "tool_name": "email.send",
            },
        },
    )
    db = _DB([row])
    authorization_calls = 0
    smtp_attempts = []

    async def authorize(*_args, **_kwargs):
        nonlocal authorization_calls
        authorization_calls += 1
        if authorization_calls == 2:
            raise RuntimeError("delegated authority revoked before SMTP")

    class _UnexpectedSMTP:
        def __init__(self, *args, **kwargs):
            smtp_attempts.append((args, kwargs))
            raise AssertionError("revoked email must not reach SMTP")

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _UnexpectedSMTP)

    await email_worker._send(str(row.id))

    assert authorization_calls == 2
    assert smtp_attempts == []
    assert row.status == "uncertain"
    assert "revoked before SMTP" in row.last_error
    assert db.commits >= 2


@pytest.mark.asyncio
async def test_email_worker_dead_letters_when_commercial_entitlement_is_inactive(monkeypatch):
    from app.core.exceptions import TenantInactiveError

    row = SimpleNamespace(
        id=uuid4(), kind="email.send", status="processing", attempts=1,
        tenant_id=uuid4(), payload={"to": ["private@example.test"], "subject": "blocked", "body": "blocked"},
        last_error=None, dead_at=None,
    )
    db = _DB([row])
    smtp_attempts = []

    async def denied(_db, *, tenant_id):
        raise TenantInactiveError("commercial entitlement expired")

    class _UnexpectedSMTP:
        def __init__(self, *args, **kwargs):
            smtp_attempts.append(args)
            raise AssertionError("ineligible email must not reach SMTP")

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr("app.services.billing_service.assert_outbound_delivery_entitlement", denied)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _UnexpectedSMTP)

    await email_worker._send(str(row.id))

    assert smtp_attempts == []
    assert row.status == "dead"
    assert row.dead_at is not None
    assert "commercial entitlement expired" in row.last_error



@pytest.mark.asyncio
async def test_agent_email_direct_and_nested_tenant_content_isolated_at_smtp(monkeypatch):
    tenants = [
        {
            "hierarchy": "direct_vendor_customer",
            "tenant_id": uuid4(),
            "agent_instance_id": uuid4(),
            "run_id": uuid4(),
            "delegation_id": uuid4(),
            "recipient": "direct-customer-ops@example.test",
            "subject": "Direct customer confidential status",
            "body": "DIRECT-CUSTOMER-ONLY tenant marker",
        },
        {
            "hierarchy": "reseller_customer",
            "tenant_id": uuid4(),
            "agent_instance_id": uuid4(),
            "run_id": uuid4(),
            "delegation_id": uuid4(),
            "recipient": "reseller-customer-ops@example.test",
            "subject": "Reseller customer confidential status",
            "body": "RESELLER-CUSTOMER-ONLY tenant marker",
        },
    ]
    rows = [
        SimpleNamespace(
            id=uuid4(),
            kind="email.send",
            status="processing",
            attempts=1,
            tenant_id=item["tenant_id"],
            last_error=None,
            dead_at=None,
            payload={
                "to": [item["recipient"]],
                "subject": item["subject"],
                "body": item["body"],
                "_agent_governance": {
                    "tenant_id": str(item["tenant_id"]),
                    "agent_instance_id": str(item["agent_instance_id"]),
                    "run_id": str(item["run_id"]),
                    "tool_name": "email.send",
                    "delegation_id": str(item["delegation_id"]),
                },
            },
        )
        for item in tenants
    ]
    databases = [_DB([row]) for row in rows]
    contexts = iter(databases)
    delivered = []
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
        assert request.tool_name == "email.send"
        assert request.required_permission == "run.execute"

    async def mark_dispatched(_db, row):
        row.status = "dispatched"

    class _CapturingSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, message):
            delivered.append(message)

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(next(contexts)))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _CapturingSMTP)
    monkeypatch.setattr(outbox_service, "mark_dispatched", mark_dispatched)

    for row in rows:
        await email_worker._send(str(row.id))

    assert len(delivered) == 2
    assert len(authorization_requests) == 4
    for index, (item, row, message) in enumerate(zip(tenants, rows, delivered, strict=True)):
        body = message.get_content()
        assert message["To"] == item["recipient"]
        assert message["Subject"] == item["subject"]
        assert item["body"] in body
        other = tenants[1 - index]
        assert other["recipient"] not in body
        assert other["subject"] not in body
        assert other["body"] not in body
        assert str(other["tenant_id"]) not in body
        assert str(other["agent_instance_id"]) not in body
        assert str(other["run_id"]) not in body
        assert str(other["delegation_id"]) not in body
        assert row.status == "dispatched"
        matching_authorizations = [
            request for request in authorization_requests
            if request.run_id == item["run_id"]
        ]
        assert len(matching_authorizations) == 2



@pytest.mark.asyncio
@pytest.mark.parametrize("hierarchy", ["direct_vendor_customer", "reseller_customer"])
async def test_agent_email_revoked_delegation_dead_letters_after_retry_exhaustion(monkeypatch, hierarchy):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from app.core import config
    from app.core.exceptions import ValidationAppError

    tenant_id, agent_id, run_id, delegation_id = uuid4(), uuid4(), uuid4(), uuid4()
    row = SimpleNamespace(
        id=uuid4(),
        kind="email.send",
        status="processing",
        attempts=1,
        tenant_id=tenant_id,
        payload={
            "to": [f"{hierarchy}@example.test"],
            "subject": f"{hierarchy} restricted",
            "body": f"{hierarchy} must never be sent",
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(agent_id),
                "run_id": str(run_id),
                "tool_name": "send_email",
                "delegation_id": str(delegation_id),
            },
        },
        last_error=None,
        dead_at=None,
        available_at=None,
    )
    db = _DB([row])
    authorization_requests = []
    smtp_attempts = []

    async def revoked(_db, request):
        authorization_requests.append(request)
        assert request.tenant_id == tenant_id
        assert request.agent_instance_id == agent_id
        assert request.run_id == run_id
        assert request.delegation_id == delegation_id
        assert request.tool_name == "send_email"
        raise ValidationAppError(f"{hierarchy} delegated grant revoked before SMTP")

    class _UnexpectedSMTP:
        def __init__(self, *args, **kwargs):
            smtp_attempts.append((args, kwargs))
            raise AssertionError("revoked Agent email must not reach SMTP")

    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(outbox_max_attempts=1))
    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", revoked)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _UnexpectedSMTP)

    await email_worker._send(str(row.id))

    assert len(authorization_requests) == 1
    assert smtp_attempts == []
    assert row.status == "dead"
    assert row.dead_at is not None
    assert isinstance(row.dead_at, datetime)
    assert row.dead_at.tzinfo == timezone.utc
    assert hierarchy in row.last_error
    assert db.commits == 1
