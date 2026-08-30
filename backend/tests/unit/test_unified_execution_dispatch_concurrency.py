"""Regression coverage for dispatch claim/finalization concurrency semantics."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def _item(status: WorkItemStatus = WorkItemStatus.ASSIGNED) -> WorkItem:
    return WorkItem(
        tenant_id=uuid.uuid4(),
        title="dispatch",
        status=status,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid.uuid4(),
        input_data={},
        policy_context={},
        idempotency_key=str(uuid.uuid4()),
    )


@pytest.mark.asyncio
async def test_claim_dispatch_uses_tenant_scoped_row_lock() -> None:
    item = _item()
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    service = UnifiedExecutionService(db)

    claimed = await service._claim_dispatch(item)

    assert claimed is item
    stmt = db.execute.await_args.args[0]
    assert stmt._for_update_arg is not None


@pytest.mark.asyncio
async def test_claim_dispatch_rejects_cancelled_item() -> None:
    item = _item(WorkItemStatus.CANCELLED)
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    service = UnifiedExecutionService(db)

    with pytest.raises(ExecutionError, match="cancelled"):
        await service._claim_dispatch(item)


@pytest.mark.asyncio
async def test_finalize_does_not_resurrect_cancelled_item() -> None:
    item = _item(WorkItemStatus.CANCELLED)
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    service = UnifiedExecutionService(db)

    current = await service._finalize_dispatch(item, {"status": "succeeded"}, WorkItemStatus.SUCCEEDED)

    assert current.status is WorkItemStatus.CANCELLED
    assert current.output_data is None
