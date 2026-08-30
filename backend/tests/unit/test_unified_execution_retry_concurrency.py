"""Regression tests for retry lifecycle idempotency semantics."""

import uuid

import pytest

from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def _failed_item(*, max_retries: int | None = None) -> WorkItem:
    return WorkItem(
        tenant_id=uuid.uuid4(), title="retry me", status=WorkItemStatus.FAILED,
        executor_type=ExecutorType.AGENT, executor_id=uuid.uuid4(), input_data={},
        policy_context={"max_retries": max_retries} if max_retries is not None else {},
        idempotency_key=str(uuid.uuid4()),
    )


def test_retry_is_single_transition_for_same_instance() -> None:
    item = _failed_item(max_retries=1)
    service = UnifiedExecutionService(None)  # type: ignore[arg-type]
    service.retry(item)
    assert item.status is WorkItemStatus.ASSIGNED
    assert item.policy_context["retry_count"] == 1
    with pytest.raises(ExecutionError, match="only failed"):
        service.retry(item)


def test_retry_enforces_max_retries() -> None:
    item = _failed_item(max_retries=1)
    item.policy_context["retry_count"] = 1
    service = UnifiedExecutionService(None)  # type: ignore[arg-type]
    with pytest.raises(ExecutionError, match="maximum retry count exceeded"):
        service.retry(item)


def test_retry_clears_previous_output_before_next_dispatch() -> None:
    item = _failed_item()
    item.output_data = {"run_id": "old-run", "status": "failed"}
    service = UnifiedExecutionService(None)  # type: ignore[arg-type]
    service.retry(item)
    assert item.status is WorkItemStatus.ASSIGNED
    assert item.output_data is None
