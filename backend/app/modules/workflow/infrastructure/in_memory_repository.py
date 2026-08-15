from __future__ import annotations
from . import __name__  # keep package import explicit
from app.modules.workflow.domain.models import WorkflowRun

class InMemoryWorkflowRunRepository:
    def __init__(self) -> None:
        self.items: dict[str, WorkflowRun] = {}

    async def get(self, run_id: str):
        return self.items.get(run_id)

    async def save(self, run: WorkflowRun):
        self.items[str(run.id)] = run
        return run
