import uuid
import pytest

from app.modules.workflow.application.service import WorkflowApplicationService
from app.modules.workflow.infrastructure.in_memory_repository import InMemoryWorkflowRunRepository


class FakeExecutor:
    called = False

    async def execute(self, workflow_id, payload):
        self.called = True
        return {"workflow_id": workflow_id, "echo": payload}


class FakeBus:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


@pytest.mark.asyncio
async def test_workflow_application_service_enqueues_without_direct_execution():
    repo = InMemoryWorkflowRunRepository()
    executor = FakeExecutor()
    enqueued = []

    async def enqueue(run):
        enqueued.append(run)

    service = WorkflowApplicationService(
        repo,
        executor,
        FakeBus(),
        enqueue_execution=enqueue,
    )

    workflow_id = str(uuid.uuid4())
    run = await service.run(workflow_id=workflow_id, payload={"x": 1})

    assert run.status == "running"
    assert len(enqueued) == 1
    assert enqueued[0] == run
    assert executor.called is False


@pytest.mark.asyncio
async def test_workflow_application_service_requires_governed_enqueue():
    repo = InMemoryWorkflowRunRepository()
    service = WorkflowApplicationService(repo)

    with pytest.raises(RuntimeError, match="enqueue is not configured"):
        await service.run(
            workflow_id=str(uuid.uuid4()),
            payload={},
        )

    assert len(repo.items) == 1
    assert next(iter(repo.items.values())).status == "running"
