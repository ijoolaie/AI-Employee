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
    def reserve(
        self, score_key: str, clock_key: str, tenant_id: str, weight: float
    ) -> tuple[float, float, bool]: ...


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
        finish, frontier_score, was_new = self.store.reserve(
            self.score_key,
            self.clock_key,
            tenant_id,
            weight,
        )
        # A newly active tenant gets the highest broker priority once so a
        # continuously busy tenant cannot monopolize all immediately queued work.
        priority = MIN_PRIORITY if was_new else _priority_from_distance(finish - frontier_score)
        return FairnessDecision(
            tenant_id=tenant_id,
            virtual_finish=finish,
            queue_priority=priority,
            weight=weight,
        )


class RedisFairnessStore:
    """Atomic Redis implementation of the tenant virtual-finish ledger."""

    _RESERVE_SCRIPT = """
    local current_raw = redis.call('ZSCORE', KEYS[1], ARGV[1])
    local was_new = current_raw == false
    local clock = redis.call('GET', KEYS[2])
    local current = tonumber(current_raw) or 0
    clock = tonumber(clock) or 0
    local start = math.max(current, clock)
    local weight = tonumber(ARGV[2])
    local finish = start + (1.0 / weight)
    redis.call('ZADD', KEYS[1], finish, ARGV[1])
    local frontier = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    local frontier_score = finish
    if #frontier >= 2 then
        frontier_score = tonumber(frontier[2])
    end
    redis.call('SET', KEYS[2], frontier_score)
    return {finish, frontier_score, was_new and 1 or 0}
    """

    def __init__(self, redis) -> None:
        self.redis = redis

    def reserve(
        self, score_key: str, clock_key: str, tenant_id: str, weight: float
    ) -> tuple[float, float, bool]:
        result = self.redis.eval(
            self._RESERVE_SCRIPT,
            2,
            score_key,
            clock_key,
            tenant_id,
            str(weight),
        )
        return float(result[0]), float(result[1]), bool(int(result[2]))


def build_redis_scheduler(redis_url: str) -> TenantFairScheduler:
    """Build the production scheduler without logging or exposing the URL."""
    from redis import Redis

    redis = Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
    )
    return TenantFairScheduler(RedisFairnessStore(redis))
