from __future__ import annotations
import uuid
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    value = _correlation_id.get()
    if value:
        return value
    value = str(uuid.uuid4())
    _correlation_id.set(value)
    return value

def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)
