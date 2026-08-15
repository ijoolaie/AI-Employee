from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ServiceHealth:
    name: str
    status: str
    latency_ms: float | None = None
    checked_at: datetime | None = None

@dataclass(frozen=True)
class SystemSnapshot:
    services: tuple[ServiceHealth, ...]
    queue_depth: int
    error_rate: float
    active_tenants: int
