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
