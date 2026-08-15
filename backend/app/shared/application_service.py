from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[Any]]

@dataclass(frozen=True)
class ApplicationService:
    name: str
    handler: Handler

    async def execute(self, payload: dict[str, Any]) -> Any:
        return await self.handler(payload)
