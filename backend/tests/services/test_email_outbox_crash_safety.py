from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import outbox_service
from app.workers import email_worker
from app.workers.email_worker import _build_email


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
async def test_claim_excludes_stale_email_delivery_from_recovery_predicate():
    db = _DB([])

    rows = await outbox_service.claim(db)

    predicate = db.statement.whereclause.compile(compile_kwargs={"literal_binds": True})
    sql = str(predicate)
    assert "email.send" in sql
    assert rows == []


@pytest.mark.asyncio
async def test_email_delivery_select_serializes_concurrent_workers(monkeypatch):
    row = SimpleNamespace(
        id=uuid4(),
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
    row = SimpleNamespace(
        id=uuid4(),
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

    monkeypatch.setattr(email_worker, "worker_db_session", lambda: _DBContext(db))
    monkeypatch.setattr(email_worker, "get_settings", lambda: _Settings())
    monkeypatch.setattr(email_worker, "assert_authorized", authorize)
    monkeypatch.setattr(email_worker.smtplib, "SMTP", _SMTP)
    monkeypatch.setattr(outbox_service, "mark_retry", fail_retry)

    await email_worker._send(str(row.id))

    assert row.status == "uncertain"
    assert "provider acceptance" in row.last_error
    assert db.commits >= 2
