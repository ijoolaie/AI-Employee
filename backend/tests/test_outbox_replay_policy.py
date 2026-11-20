from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import outbox_service


@pytest.mark.asyncio
async def test_replay_resets_retry_budget_and_terminal_delivery_metadata():
    message = SimpleNamespace(
        status="dead",
        attempts=8,
        available_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        dispatched_at=datetime(2020, 1, 2, tzinfo=timezone.utc),
        last_error="provider unavailable",
        dead_at=datetime(2020, 1, 3, tzinfo=timezone.utc),
        replayed_at=None,
    )

    class _DB:
        flushed = False

        async def flush(self):
            self.flushed = True

    db = _DB()
    result = await outbox_service.replay(db, message)

    assert result is message
    assert message.status == "pending"
    assert message.attempts == 0
    assert message.available_at <= datetime.now(timezone.utc)
    assert message.dispatched_at is None
    assert message.last_error is None
    assert message.dead_at is None
    assert message.replayed_at == message.available_at
    assert db.flushed is True
