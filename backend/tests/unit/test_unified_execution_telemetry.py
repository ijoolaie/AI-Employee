from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import UnifiedExecutionService


class DispatchDb:
    def __init__(self, work_item):
        self.work_item = work_item

    async def execute(self, *_args):
        return SimpleNamespace(scalar_one_or_none=lambda: self.work_item)

    async def flush(self):
        return None

    async def commit(self):
        return None


class FakeHuman:
    def dispatch(self, work_item):
        return {"ok": True}


@pytest.mark.asyncio
async def test_execution_dispatch_emits_correlated_telemetry():
    item = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        status=WorkItemStatus.READY,
        executor_type=ExecutorType.HUMAN,
        executor_id=uuid4(),
        output_data=None,
        policy_context={},
    )
    service = UnifiedExecutionService(DispatchDb(item), human_executor=FakeHuman())

    await service.dispatch(item)

    events = service.telemetry.events
    assert [event.event for event in events] == ["started", "dispatched"]
    assert all(event.work_item_id == item.id for event in events)
    assert all(event.tenant_id == item.tenant_id for event in events)


@pytest.mark.asyncio
async def test_execution_failure_emits_failed_telemetry():
    class BrokenHuman:
        def dispatch(self, work_item):
            raise RuntimeError("boom")

    item = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        status=WorkItemStatus.READY,
        executor_type=ExecutorType.HUMAN,
        executor_id=uuid4(),
        output_data=None,
        policy_context={},
    )
    service = UnifiedExecutionService(DispatchDb(item), human_executor=BrokenHuman())

    with pytest.raises(RuntimeError, match="boom"):
        await service.dispatch(item)

    assert [event.event for event in service.telemetry.events] == ["started", "failed"]
