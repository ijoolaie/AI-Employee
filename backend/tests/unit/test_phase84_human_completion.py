from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def human_item():
    executor_id = uuid4()
    return SimpleNamespace(
        id=uuid4(),
        executor_type=ExecutorType.HUMAN,
        executor_id=executor_id,
        status=WorkItemStatus.RUNNING,
        output_data={},
        policy_context={},
    ), executor_id


def test_phase84_human_completion_requires_owner():
    item, owner = human_item()
    service = UnifiedExecutionService(SimpleNamespace())

    service.complete_human(item, executor_id=owner, output={"result": "done"})

    assert item.status is WorkItemStatus.SUCCEEDED
    assert item.output_data == {"result": "done"}


def test_phase84_human_completion_rejects_other_executor():
    item, _owner = human_item()
    service = UnifiedExecutionService(SimpleNamespace())

    with pytest.raises(ExecutionError, match="does not own"):
        service.complete_human(item, executor_id=uuid4())
