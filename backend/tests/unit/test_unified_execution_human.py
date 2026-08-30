from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.human_execution import HumanExecutionAdapter
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


class DispatchDb:
    def __init__(self, work_item):
        self.work_item = work_item

    async def execute(self, *_args):
        return SimpleNamespace(scalar_one_or_none=lambda: self.work_item)

    async def flush(self):
        return None

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_phase84_human_dispatch_waits_for_explicit_completion():
    executor_id = uuid4()
    item = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status=WorkItemStatus.READY,
        executor_type=None, executor_id=None, output_data=None, policy_context={},
    )
    service = UnifiedExecutionService(DispatchDb(item), human_executor=HumanExecutionAdapter())

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
