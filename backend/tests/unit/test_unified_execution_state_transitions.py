"""Regression coverage for WorkItem cancellation state transitions."""

from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def _item(status: WorkItemStatus) -> WorkItem:
    return WorkItem(
        tenant_id=uuid4(),
        title="state transition",
        status=status,
        executor_type=ExecutorType.HUMAN,
        executor_id=uuid4(),
        input_data={},
        policy_context={},
        idempotency_key=str(uuid4()),
    )


@pytest.mark.parametrize(
    "status",
    [
        WorkItemStatus.READY,
        WorkItemStatus.ASSIGNED,
        WorkItemStatus.RUNNING,
        WorkItemStatus.BLOCKED,
        WorkItemStatus.WAITING_APPROVAL,
    ],
)
def test_cancel_allows_non_terminal_active_states(status: WorkItemStatus) -> None:
    item = _item(status)

    result = UnifiedExecutionService(None).cancel(item)  # type: ignore[arg-type]

    assert result is item
    assert item.status is WorkItemStatus.CANCELLED


@pytest.mark.parametrize(
    "status",
    [WorkItemStatus.DRAFT, WorkItemStatus.SUCCEEDED, WorkItemStatus.CANCELLED],
)
def test_cancel_rejects_forbidden_states(status: WorkItemStatus) -> None:
    item = _item(status)

    with pytest.raises(ExecutionError):
        UnifiedExecutionService(None).cancel(item)  # type: ignore[arg-type]

    assert item.status is status


def test_retry_rejects_failed_item_without_executor() -> None:
    item = _item(WorkItemStatus.FAILED)
    item.executor_type = None
    item.executor_id = None

    with pytest.raises(ExecutionError, match="no executor"):
        UnifiedExecutionService(None).retry(item)  # type: ignore[arg-type]

    assert item.status is WorkItemStatus.FAILED
