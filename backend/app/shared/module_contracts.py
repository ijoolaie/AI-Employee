from __future__ import annotations
from typing import Any, Protocol

class ModuleCommandBus(Protocol):
    async def dispatch(self, module: str, command: str, payload: dict[str, Any]) -> Any:
        ...

class ModuleQueryBus(Protocol):
    async def ask(self, module: str, query: str, payload: dict[str, Any]) -> Any:
        ...

class EventPublisher(Protocol):
    async def publish(self, event: Any) -> None:
        ...
