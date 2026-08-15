from __future__ import annotations
from typing import Any, Protocol
from .models import WorkflowRun

class WorkflowRunRepository(Protocol):
    async def get(self, run_id: str) -> WorkflowRun | None: ...
    async def save(self, run: WorkflowRun) -> WorkflowRun: ...

class WorkflowExecutor(Protocol):
    async def execute(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
