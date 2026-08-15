from typing import Any, Protocol

class TaskQueue(Protocol):
    async def enqueue(self, task_name: str, payload: dict[str, Any], *, task_id: str | None = None) -> str: ...

class EventBus(Protocol):
    async def publish(self, event: Any) -> None: ...
