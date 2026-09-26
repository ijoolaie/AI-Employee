from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import workflow_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


@pytest.mark.asyncio
async def test_parent_child_execution_guard_locks_and_rejects_cancelled_run():
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_Result(SimpleNamespace(status="cancelled")))
    )

    with pytest.raises(
        workflow_service.ValidationAppError,
        match="WORKFLOW_PARENT_NOT_RUNNING:cancelled",
    ):
        await workflow_service._lock_parent_for_child_execution(
            db,
            workflow_run_id="run-1",
        )

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_parent_child_execution_guard_allows_running_run():
    run = SimpleNamespace(status="running")
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_Result(run))
    )

    result = await workflow_service._lock_parent_for_child_execution(
        db,
        workflow_run_id="run-1",
    )

    assert result is run
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_parent_child_execution_guard_times_out_before_side_effect():
    from datetime import datetime, timedelta, timezone

    run = SimpleNamespace(
        status="running",
        deadline_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        error=None,
        completed_at=None,
        tenant_id="tenant-1",
        id="run-1",
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_Result(run)),
        flush=AsyncMock(),
    )
    audit = AsyncMock()
    original = workflow_service.audit_service.record
    workflow_service.audit_service.record = audit
    try:
        result = await workflow_service._lock_parent_for_child_execution(
            db,
            workflow_run_id="run-1",
        )
    finally:
        workflow_service.audit_service.record = original

    assert result is run
    assert run.status == "timed_out"
    assert run.error["code"] == "WORKFLOW_TIMEOUT"
    db.flush.assert_awaited_once()
    audit.assert_awaited_once()
