from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.human_execution import HumanExecutionAdapter
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


@pytest.mark.asyncio
async def test_phase84_human_dispatch_waits_for_explicit_completion():
    executor_id = uuid4()
    item = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status=WorkItemStatus.READY,
        executor_type=None, executor_id=None, output_data=None, policy_context={},
    )
    service = UnifiedExecutionService(SimpleNamespace(), human_executor=HumanExecutionAdapter())

    service.assign_human(item, executor_id)
    result = await service.dispatch(item)

    assert result.dispatched is True
    assert item.status is WorkItemStatus.RUNNING
    assert item.output_data["status"] == "awaiting_human_action"

    service.complete_human(item, executor_id=executor_id, output={"approved": True})
    assert item.status is WorkItemStatus.SUCCEEDED
    assert item.output_data == {"approved": True}


def test_phase84_human_completion_is_owner_scoped():
    executor_id = uuid4()
    item = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status=WorkItemStatus.RUNNING,
        executor_type=ExecutorType.HUMAN, executor_id=executor_id,
        output_data={}, policy_context={},
    )
    service = UnifiedExecutionService(SimpleNamespace())

    with pytest.raises(ExecutionError, match="does not own"):
        service.complete_human(item, executor_id=uuid4())
