"""Distributed tenant-fair admission/routing primitives."""
from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Protocol

DEFAULT_TENANT_WEIGHT = 1.0
MIN_PRIORITY = 0
MAX_PRIORITY = 9
DEFAULT_PRIORITY = 4


class FairnessStore(Protocol):
    def get(self, key: str): ...
    def set(self, key: str, value, **kwargs): ...
    def zscore(self, key: str, member: str): ...
    def zadd(self, key: str, mapping: dict[str, float]): ...
    def zrange(self, key: str, start: int, end: int, withscores: bool = False): ...


@dataclass(frozen=True)
class FairnessDecision:
    tenant_id: str
    virtual_finish: float
    queue_priority: int
    weight: float


def _priority_from_distance(distance: float) -> int:
    """Map virtual-finish distance to Redis/Celery's bounded 0..9 priority."""
    return max(MIN_PRIORITY, min(MAX_PRIORITY, floor(max(distance, 0.0))))


class TenantFairScheduler:
    """Weighted fair-queueing ledger suitable for a Celery producer/router."""

    def __init__(self, store: FairnessStore, *, key_prefix: str = "aiep:fair") -> None:
        self.store = store
        self.key_prefix = key_prefix

    @property
    def score_key(self) -> str:
        return f"{self.key_prefix}:virtual-finish"

    @property
    def clock_key(self) -> str:
        return f"{self.key_prefix}:virtual-clock"

    def route(self, tenant_id: str, *, weight: float = DEFAULT_TENANT_WEIGHT) -> FairnessDecision:
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required for fair scheduling")
        if weight <= 0:
            raise ValueError("tenant weight must be positive")

        tenant_id = tenant_id.strip()
        current = self.store.zscore(self.score_key, tenant_id)
        clock = self.store.get(self.clock_key)
        current_score = float(current) if current is not None else 0.0
        virtual_clock = float(clock) if clock is not None else 0.0

        start = max(current_score, virtual_clock)
        finish = start + (1.0 / weight)
        self.store.zadd(self.score_key, {tenant_id: finish})
        self.store.set(self.clock_key, str(min(start, finish)))

        frontier = self.store.zrange(self.score_key, 0, 0, withscores=True)
        frontier_score = float(frontier[0][1]) if frontier else start
        return FairnessDecision(
            tenant_id=tenant_id,
            virtual_finish=finish,
            queue_priority=_priority_from_distance(finish - frontier_score),
            weight=weight,
        )


def build_redis_scheduler(redis_url: str) -> TenantFairScheduler:
    """Build the production scheduler without logging or exposing the URL."""
    from redis import Redis

    store = Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
    )
    return TenantFairScheduler(store)
