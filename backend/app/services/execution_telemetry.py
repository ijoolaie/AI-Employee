"""Execution telemetry primitives for Phase 8.6."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ExecutionEvent:
    tenant_id: UUID
    work_item_id: UUID
    event: str
    duration_ms: float | None = None
    cost: float | None = None
    tokens: int | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class ExecutionTelemetry:
    """In-memory structured event sink; callers may replace it with durable storage."""

    def __init__(self) -> None:
        self.events: list[ExecutionEvent] = []

    def emit(self, event: ExecutionEvent) -> ExecutionEvent:
        safe_metadata = {
            key: value
            for key, value in (event.metadata or {}).items()
            if "secret" not in key.lower() and "token" not in key.lower() and "password" not in key.lower()
        }
        safe_event = ExecutionEvent(
            tenant_id=event.tenant_id,
            work_item_id=event.work_item_id,
            event=event.event,
            duration_ms=event.duration_ms,
            cost=event.cost,
            tokens=event.tokens,
            correlation_id=event.correlation_id,
            metadata=safe_metadata,
        )
        self.events.append(safe_event)
        return safe_event

    @staticmethod
    def started() -> float:
        return perf_counter()

    @staticmethod
    def elapsed_ms(start: float) -> float:
        return round((perf_counter() - start) * 1000, 3)
