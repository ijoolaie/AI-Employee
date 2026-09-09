from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.outbox import OutboxMessage
from app.services import outbox_service
from app.workers.email_worker import _build_email


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _DB:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _Result(self.rows)

    async def flush(self):
        return None


class _Settings:
    smtp_from_email = "noreply@example.test"


def test_email_message_id_is_stable_for_outbox_item():
    payload = {"to": ["user@example.test"], "subject": "Hello", "body": "Body"}
    outbox_id = str(uuid4())

    first = _build_email(payload, outbox_id, _Settings())
    second = _build_email(payload, outbox_id, _Settings())

    assert first["Message-ID"] == second["Message-ID"]
    assert outbox_id in first["Message-ID"]


@pytest.mark.asyncio
async def test_claim_does_not_reclaim_stale_email_delivery():
    stale_email = OutboxMessage(
        kind="email.send",
        payload={},
        status="processing",
        attempts=1,
        available_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    db = _DB([stale_email])

    rows = await outbox_service.claim(db)

    # The fake DB returns the row regardless of SQL filtering; inspect the
    # generated predicate to ensure email.send is excluded from stale recovery.
    assert "email.send" in str(db.statement.whereclause)
    assert "available_at" in str(db.statement.whereclause)
    assert rows == [stale_email]
    assert stale_email.status == "processing"
