"""Regression coverage for WorkItem cancellation state transitions."""

from uuid import uuid4

import pytest

from app.models.run import Run
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


class _Result:
    def __init__(self, *, rows=()):
        self._rows = list(rows)

    def scalars(self):
        return self

    def all(self):
        return self._rows


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


class _CancelDB:
    def __init__(self, children, grand_children, runs):
        self.results = [
            _Result(rows=children),
            _Result(rows=grand_children),
            _Result(rows=[]),
            _Result(rows=[run for run in runs if run.status in {"pending", "waiting"}]),
        ]

    async def execute(self, _statement):
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_cancel_with_descendants_cancels_active_children_and_queued_runs() -> None:
    tenant_id = uuid4()
    parent = _item(WorkItemStatus.RUNNING)
    parent.tenant_id = tenant_id
    child = _item(WorkItemStatus.ASSIGNED)
    child.tenant_id = tenant_id
    child.parent_work_item_id = parent.id
    grandchild = _item(WorkItemStatus.WAITING_APPROVAL)
    grandchild.tenant_id = tenant_id
    grandchild.parent_work_item_id = child.id
    child_run = Run(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid4(),
        employee_version_id=uuid4(),
        work_item_id=child.id,
        status="pending",
        input_data={},
    )
    grandchild_run = Run(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid4(),
        employee_version_id=uuid4(),
        work_item_id=grandchild.id,
        status="waiting",
        input_data={},
    )
    terminal_run = Run(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid4(),
        employee_version_id=uuid4(),
        work_item_id=grandchild.id,
        status="success",
        input_data={},
    )
    db = _CancelDB([child], [grandchild], [child_run, grandchild_run, terminal_run])
    service = UnifiedExecutionService(db)  # type: ignore[arg-type]

    await service.cancel_with_descendants(parent)

    assert parent.status is WorkItemStatus.CANCELLED
    assert child.status is WorkItemStatus.CANCELLED
    assert grandchild.status is WorkItemStatus.CANCELLED
    assert child_run.status == "cancelled"
    assert grandchild_run.status == "cancelled"
    assert terminal_run.status == "success"
