import uuid
import pytest

from app.modules.workflow.application.service import WorkflowApplicationService
from app.modules.workflow.infrastructure.in_memory_repository import InMemoryWorkflowRunRepository

class FakeExecutor:
    async def execute(self, workflow_id, payload):
        return {"workflow_id": workflow_id, "echo": payload}

class FakeBus:
    def __init__(self):
        self.events = []
    async def publish(self, event):
        self.events.append(event)

@pytest.mark.asyncio
async def test_workflow_application_service_runs_and_publishes_event():
    repo = InMemoryWorkflowRunRepository()
    bus = FakeBus()
    service = WorkflowApplicationService(repo, FakeExecutor(), bus)

    workflow_id = str(uuid.uuid4())
    run = await service.run(
        workflow_id=workflow_id,
        payload={"x": 1},
    )

    assert run.status == "completed"
    assert run.output["echo"] == {"x": 1}
    assert len(bus.events) == 1
    assert bus.events[0].name == "workflow.run.completed"
    assert await repo.get(str(run.id)) == run

@pytest.mark.asyncio
async def test_workflow_failure_is_recorded():
    class FailingExecutor:
        async def execute(self, workflow_id, payload):
            raise RuntimeError("boom")

    repo = InMemoryWorkflowRunRepository()
    bus = FakeBus()
    service = WorkflowApplicationService(repo, FailingExecutor(), bus)

    workflow_id = str(uuid.uuid4())
    with pytest.raises(RuntimeError):
        await service.run(workflow_id=workflow_id, payload={})

    assert len(repo.items) == 1
    assert next(iter(repo.items.values())).status == "failed"
    assert bus.events == []
