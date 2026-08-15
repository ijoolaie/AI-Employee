from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from app.shared.correlation import get_correlation_id

@dataclass(frozen=True)
class OperationMetric:
    name: str
    duration_ms: float
    correlation_id: str

class OperationTimer:
    def __init__(self, name: str):
        self.name = name
        self.started = 0.0

    def __enter__(self):
        self.started = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.metric = OperationMetric(
            self.name,
            (perf_counter() - self.started) * 1000,
            get_correlation_id(),
        )
