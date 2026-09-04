"""Runtime evidence for Phase 14.12 tenant fairness and resource isolation.

These tests use the Redis service provided by CI so the production Lua admission
paths are exercised rather than a mocked implementation.
"""
from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from redis import Redis

from app.services.tenant_fair_scheduler import TenantFairScheduler, RedisFairnessStore
from app.services.tenant_resource_limiter import TenantResourceLimiter


@pytest.fixture
def redis_client() -> Redis:
    client = Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
    )
    try:
        client.ping()
    except Exception as exc:  # pragma: no cover - CI service contract
        pytest.skip(f"Redis runtime evidence service unavailable: {exc}")
    client.flushdb()
    try:
        yield client
    finally:
        client.flushdb()
        client.close()


def test_runtime_concurrency_cap_and_cross_tenant_isolation(redis_client: Redis, capsys) -> None:
    """Sustained concurrent admission never exceeds each tenant's configured cap."""
    limiter = TenantResourceLimiter(
        redis_client,
        {"tenant-a": 2, "tenant-b": 1},
        default_limit=1,
        lease_seconds=10,
    )

    lock = threading.Lock()
    active = {"tenant-a": 0, "tenant-b": 0}
    maximum = {"tenant-a": 0, "tenant-b": 0}
    admitted = {"tenant-a": 0, "tenant-b": 0}

    def worker(tenant_id: str) -> None:
        lease = limiter.acquire(tenant_id)
        if lease is None:
            return
        with lock:
            active[tenant_id] += 1
            maximum[tenant_id] = max(maximum[tenant_id], active[tenant_id])
            admitted[tenant_id] += 1
        time.sleep(0.03)
        with lock:
            active[tenant_id] -= 1
        limiter.release(lease)

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(worker, "tenant-a") for _ in range(8)]
        futures += [pool.submit(worker, "tenant-b") for _ in range(4)]
        for future in futures:
            future.result()

    assert maximum == {"tenant-a": 2, "tenant-b": 1}
    assert admitted["tenant-a"] == 2
    assert admitted["tenant-b"] == 1
    print(
        "RUNTIME_EVIDENCE|resource_caps|PASS|"
        f"tenant-a_max={maximum['tenant-a']}|tenant-b_max={maximum['tenant-b']}|"
        f"admitted_a={admitted['tenant-a']}|admitted_b={admitted['tenant-b']}"
    )
    capsys.readouterr()


def test_runtime_fair_scheduler_prevents_busy_tenant_from_starving_newcomer(
    redis_client: Redis, capsys
) -> None:
    """Real Redis reservations keep a newcomer at highest priority once admitted."""
    scheduler = TenantFairScheduler(
        RedisFairnessStore(redis_client),
        key_prefix="aiep:test:phase-14-12:fair",
    )

    busy_decisions = [scheduler.route("busy") for _ in range(20)]
    newcomer = scheduler.route("newcomer")
    later_busy = scheduler.route("busy")

    assert newcomer.queue_priority == 0
    assert newcomer.queue_priority < later_busy.queue_priority
    assert newcomer.virtual_finish == pytest.approx(21.0)
    assert busy_decisions[-1].virtual_finish == pytest.approx(20.0)

    print(
        "RUNTIME_EVIDENCE|fairness|PASS|"
        f"busy_reservations={len(busy_decisions)}|"
        f"newcomer_priority={newcomer.queue_priority}|"
        f"later_busy_priority={later_busy.queue_priority}|"
        f"newcomer_finish={newcomer.virtual_finish:.1f}"
    )
    capsys.readouterr()


def test_runtime_weighted_scheduler_preserves_service_share_signal(redis_client: Redis) -> None:
    """A heavier tenant receives smaller virtual-finish increments under sustained load."""
    scheduler = TenantFairScheduler(
        RedisFairnessStore(redis_client),
        key_prefix="aiep:test:phase-14-12:weighted",
    )

    light = [scheduler.route("light", weight=1.0) for _ in range(20)]
    heavy = [scheduler.route("heavy", weight=2.0) for _ in range(20)]

    light_increment = light[-1].virtual_finish / len(light)
    heavy_increment = heavy[-1].virtual_finish / len(heavy)
    assert light_increment == pytest.approx(1.0)
    assert heavy_increment == pytest.approx(0.5)
    assert heavy_increment < light_increment
