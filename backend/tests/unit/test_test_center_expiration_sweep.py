"""P12.5 automatic Test Center expiration sweep tests."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.test_run import TestRunStatus
from app.services.test_center import TestCenterError, TestCenterService


class Result:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def all(self):
        return self.value or []


class SweepDB:
    def __init__(self, candidates):
        self.candidates = candidates

    async def execute(self, _statement):
        return Result(self.candidates)


async def _fake_expire_run(*, run_id, tenant_id, timeout_seconds, now):
    del run_id, tenant_id, timeout_seconds
    run = _fake_expire_run.run
    run.status = TestRunStatus.EXPIRED
    run.finished_at = now
    run.error = "test run expired"
    return run


@pytest.mark.asyncio
async def test_expire_stale_runs_expires_queued_candidates_at_cutoff():
    tenant_id = uuid4()
    now = datetime(2026, 9, 3, 6, 0, tzinfo=timezone.utc)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.QUEUED,
        queued_at=now - timedelta(seconds=60), started_at=None,
        finished_at=None, error=None,
    )
    _fake_expire_run.run = run
    service = TestCenterService(SweepDB([run]))
    service.expire_run = _fake_expire_run

    expired = await service.expire_stale_runs(
        timeout_seconds=60,
        now=now,
        batch_size=200,
    )

    assert expired == [run]
    assert run.status is TestRunStatus.EXPIRED
    assert run.finished_at == now
    assert run.error == "test run expired"


@pytest.mark.asyncio
async def test_expire_stale_runs_uses_started_at_for_running_candidates():
    tenant_id = uuid4()
    now = datetime(2026, 9, 3, 6, 0, tzinfo=timezone.utc)
    run = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=TestRunStatus.RUNNING,
        queued_at=now - timedelta(hours=2), started_at=now - timedelta(seconds=60),
        finished_at=None, error=None,
    )
    _fake_expire_run.run = run
    service = TestCenterService(SweepDB([run]))
    service.expire_run = _fake_expire_run

    expired = await service.expire_stale_runs(
        timeout_seconds=60,
        now=now,
        batch_size=200,
    )

    assert expired == [run]
    assert run.status is TestRunStatus.EXPIRED


@pytest.mark.asyncio
async def test_expire_stale_runs_rejects_invalid_batch_size():
    with pytest.raises(TestCenterError, match="batch size"):
        await TestCenterService(SweepDB([])).expire_stale_runs(
            timeout_seconds=60,
            batch_size=0,
        )
