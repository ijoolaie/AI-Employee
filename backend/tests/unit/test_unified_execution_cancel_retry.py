from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def item(status, *, retries=None, max_retries=None):
    context = {}
    if retries is not None:
        context["retry_count"] = retries
    if max_retries is not None:
        context["max_retries"] = max_retries
    return SimpleNamespace(
        id=uuid4(), status=status, executor_type=ExecutorType.AGENT,
        executor_id=uuid4(), output_data={"run_id": "run-1"}, policy_context=context,
    )


def service():
    return UnifiedExecutionService(SimpleNamespace())


def test_cancel_active_item():
    work = item(WorkItemStatus.RUNNING)
    service().cancel(work)
    assert work.status is WorkItemStatus.CANCELLED


def test_cancel_terminal_item_is_rejected():
    work = item(WorkItemStatus.SUCCEEDED)
    with pytest.raises(ExecutionError, match="terminal"):
        service().cancel(work)


def test_retry_failed_item_resets_execution_and_increments_count():
    work = item(WorkItemStatus.FAILED, retries=1, max_retries=3)
    service().retry(work)
    assert work.status is WorkItemStatus.ASSIGNED
    assert work.output_data is None
    assert work.policy_context["retry_count"] == 2


def test_retry_only_failed_items():
    work = item(WorkItemStatus.RUNNING)
    with pytest.raises(ExecutionError, match="only failed"):
        service().retry(work)


def test_retry_respects_maximum():
    work = item(WorkItemStatus.FAILED, retries=2, max_retries=2)
    with pytest.raises(ExecutionError, match="maximum retry"):
        service().retry(work)
