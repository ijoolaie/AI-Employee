"""Structured (JSON) logging + request-scoped context.

Per docs v1.2 §6 and 04_Architecture goal #4: Observability (Trace, Cost,
Replay) is a non-removable MVP requirement, not something bolted on later.
This module is the baseline layer — every log line carries request_id /
tenant_id / user_id when available, so logs from day one are already
correlatable with `audit_logs` (request_id) and later with `runs` /
`run_traces` (Employee Framework §5, §8).
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from typing import Any

from app.core.privacy import redact_sensitive_data

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
tenant_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_id", default=None
)
user_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)


def new_request_id() -> str:
    return uuid.uuid4().hex


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "tenant_id": tenant_id_var.get(),
            "user_id": user_id_var.get(),
        }
        # Allow ad-hoc structured fields: logger.info("msg", extra={"cost_usd": 0.002})
        for key, value in record.__dict__.items():
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName", "taskName",
            ):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(redact_sensitive_data(payload), default=str)


def configure_logging(debug: bool = False) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)


class Timer:
    """Small helper for latency measurement, used by the AI Gateway and
    Workflow/Run execution to record duration_ms consistently."""

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        self.duration_ms: float = 0.0
        return self

    @property
    def elapsed_ms(self) -> float:
        """Return the elapsed time while the context is still active.

        ``duration_ms`` is finalized in ``__exit__``. Callers that need the
        duration from inside a ``try/finally`` block must use this property,
        because ``finally`` runs before the context manager's ``__exit__``.
        """
        if hasattr(self, "_start"):
            return (time.perf_counter() - self._start) * 1000
        return self.duration_ms

    def __exit__(self, *exc: Any) -> None:
        self.duration_ms = self.elapsed_ms
