from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable
import uuid

@dataclass(frozen=True)
class DomainEvent:
    name: str
    tenant_id: uuid.UUID | None
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

EventHandler = Callable[[DomainEvent], Awaitable[None]]

class InProcessEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.name, []):
            await handler(event)
