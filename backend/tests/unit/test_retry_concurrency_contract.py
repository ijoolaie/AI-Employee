"""Contract coverage for retry concurrency assumptions."""

import uuid

import pytest

from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def _failed_item() -> WorkItem:
    return WorkItem(
        tenant_id=uuid.uuid4(),
        title="retry",
        status=WorkItemStatus.FAILED,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid.uuid4(),
        input_data={},
        policy_context={},
        idempotency_key=str(uuid.uuid4()),
    )


def test_retry_requires_failed_state() -> None:
    item = _failed_item()
    service = UnifiedExecutionService(None)  # type: ignore[arg-type]
    service.retry(item)
    with pytest.raises(ExecutionError, match="only failed"):
        service.retry(item)


def test_retry_is_not_a_new_execution() -> None:
    item = _failed_item()
    service = UnifiedExecutionService(None)  # type: ignore[arg-type]
    service.retry(item)
    assert item.status is WorkItemStatus.ASSIGNED
    assert item.output_data is None
    assert item.policy_context["retry_count"] == 1
