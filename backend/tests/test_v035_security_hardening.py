from datetime import datetime, timezone, timedelta

from app.services.workflow_trigger_service import verify_replay_timestamp


def test_webhook_replay_timestamp_accepts_current_timestamp():
    now = datetime.now(timezone.utc)
    assert verify_replay_timestamp(str(int(now.timestamp())), now=now)


def test_webhook_replay_timestamp_rejects_stale_timestamp():
    now = datetime.now(timezone.utc)
    stale = int((now - timedelta(seconds=301)).timestamp())
    assert not verify_replay_timestamp(str(stale), now=now)


def test_webhook_replay_timestamp_rejects_missing_and_invalid():
    assert not verify_replay_timestamp(None)
    assert not verify_replay_timestamp("not-a-timestamp")
