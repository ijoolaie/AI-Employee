from __future__ import annotations
from typing import Any

class LegacyWorkflowExecutor:
    """Adapter point for the existing RC8 workflow engine.

    The existing implementation remains the source of behavior; this adapter
    makes the application layer independent from its concrete location.
    """
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    async def execute(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self.legacy_service.execute(workflow_id, payload)
        return result if isinstance(result, dict) else {"result": result}
