from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services import outbox_service


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _Scalars(self._rows)


class _Session:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None
        self.flushed = False

    async def execute(self, statement):
        self.statement = statement
        return _Result(self.rows)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_claim_starts_processing_lease_at_claim_time():
    old_due_time = datetime.now(timezone.utc) - timedelta(minutes=4)
    row = SimpleNamespace(
        status="pending",
        attempts=0,
        available_at=old_due_time,
        kind="workforce.assignment.execute",
    )
    db = _Session([row])

    claimed = await outbox_service.claim(db, limit=10)

    assert claimed == [row]
    assert row.status == "processing"
    assert row.attempts == 1
    assert row.available_at > old_due_time
    assert datetime.now(timezone.utc) - row.available_at < timedelta(seconds=5)
    assert db.flushed