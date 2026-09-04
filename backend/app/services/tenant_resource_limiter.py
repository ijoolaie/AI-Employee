"""Redis-backed tenant resource leases with crash-safe expiry."""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger("app.services.tenant_resource_limiter")

_ACQUIRE_SCRIPT = """
local now = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('ZCARD', KEYS[1]) >= limit then
    return 0
end
redis.call('ZADD', KEYS[1], tonumber(ARGV[1]), ARGV[4])
return 1
"""
_RELEASE_SCRIPT = """
return redis.call('ZREM', KEYS[1], ARGV[1])
"""


@dataclass(frozen=True)
class ResourceLease:
    tenant_id: str
    token: str
    expires_at: float


class TenantResourceLimitError(RuntimeError):
    """Raised when a tenant has no available execution resource slot."""


class TenantResourceLimiter:
    """Enforce a bounded number of concurrent execution leases per tenant."""

    def __init__(self, redis: Redis, limits: dict[str, int], default_limit: int, lease_seconds: int) -> None:
        if default_limit < 1:
            raise ValueError("default_limit must be positive")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        self._redis = redis
        self._limits = limits
        self._default_limit = default_limit
        self._lease_seconds = lease_seconds

    def limit_for(self, tenant_id: str) -> int:
        limit = self._limits.get(tenant_id, self._default_limit)
        if limit < 1:
            raise ValueError("tenant resource concurrency limit must be positive")
        return limit

    def acquire(self, tenant_id: str) -> ResourceLease | None:
        token = uuid.uuid4().hex
        now = time.time()
        expires_at = now + self._lease_seconds
        key = f"aiep:tenant-resource:{tenant_id}"
        acquired = self._redis.eval(
            _ACQUIRE_SCRIPT,
            1,
            key,
            expires_at,
            now,
            self.limit_for(tenant_id),
            token,
        )
        if int(acquired) != 1:
            return None
        return ResourceLease(tenant_id=tenant_id, token=token, expires_at=expires_at)

    def release(self, lease: ResourceLease) -> None:
        key = f"aiep:tenant-resource:{lease.tenant_id}"
        self._redis.eval(_RELEASE_SCRIPT, 1, key, lease.token)


def build_tenant_resource_limiter() -> TenantResourceLimiter:
    settings = get_settings()
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
    )
    return TenantResourceLimiter(
        redis=redis,
        limits=settings.tenant_resource_concurrency,
        default_limit=settings.tenant_resource_default_concurrency,
        lease_seconds=settings.tenant_resource_lease_seconds,
    )
