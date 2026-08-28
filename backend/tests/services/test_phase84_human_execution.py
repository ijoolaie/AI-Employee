from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.human_execution import HumanExecutionAdapter
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


@pytest.mark.asyncio
async def test_phase84_human_dispatch_keeps_work_item_running():
    executor_id = uuid4()
    work_item = SimpleNamespace(
        tenant_id=uuid4(),
        executor_type=ExecutorType.HUMAN,
        executor_id=executor_id,
        status=WorkItemStatus.ASSIGNED,
        output_data=None,
        policy_context={},
    )
    service = UnifiedExecutionService(None, human_executor=HumanExecutionAdapter())

    result = await service.dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.RUNNING
    assert work_item.output_data["state"] == "awaiting_human"
    assert work_item.output_data["executor_id"] == str(executor_id)


def test_phase84_human_completion_requires_assigned_executor():
    executor_id = uuid4()
    other_executor = uuid4()
    work_item = SimpleNamespace(
        executor_type=ExecutorType.HUMAN,
        executor_id=executor_id,
        status=WorkItemStatus.RUNNING,
        output_data=None,
    )
    service = UnifiedExecutionService(None)

    with pytest.raises(ExecutionError, match="does not own"):
        service.complete_human(work_item, executor_id=other_executor, output={"answer": "no"})

    service.complete_human(work_item, executor_id=executor_id, output={"answer": "yes"})

    assert work_item.status is WorkItemStatus.SUCCEEDED
    assert work_item.output_data == {"answer": "yes"}


def test_phase84_human_failure_is_explicit_and_owner_scoped():
    executor_id = uuid4()
    work_item = SimpleNamespace(
        executor_type=ExecutorType.HUMAN,
        executor_id=executor_id,
        status=WorkItemStatus.ASSIGNED,
        output_data=None,
    )
    service = UnifiedExecutionService(None)

    service.fail_human(work_item, executor_id=executor_id, output={"reason": "cancelled by user"})

    assert work_item.status is WorkItemStatus.FAILED
    assert work_item.output_data["reason"] == "cancelled by user"
