"""Synthetic load and capacity evidence for Phase 14.13.

The suite is intentionally bounded and reproducible. It validates the production
routing/admission primitives against explicit thresholds without claiming that a
CI runner is a production capacity environment.
"""
from __future__ import annotations

import json
import os
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from redis import Redis

from app.main import app
from app.services.tenant_fair_scheduler import RedisFairnessStore, TenantFairScheduler
from app.services.tenant_resource_limiter import TenantResourceLimiter
from app.workers.celery_app import EXECUTION_QUEUE, tenant_fair_route


ARTIFACT_DIR = Path(os.environ.get("PHASE_14_13_ARTIFACT_DIR", "artifacts/phase-14-13"))


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
        pytest.skip(f"Redis load evidence service unavailable: {exc}")
    client.flushdb()
    try:
        yield client
    finally:
        client.flushdb()
        client.close()


def _write_evidence(name: str, payload: dict[str, object]) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACT_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_api_health_bounded_concurrent_load(capsys) -> None:
    """The health API remains responsive under a bounded concurrent burst."""
    requests = 240
    workers = 12
    latencies: list[float] = []
    failures: list[str] = []
    lock = threading.Lock()

    with TestClient(app) as client:
        def request() -> None:
            started = time.perf_counter()
            response = client.get("/health")
            elapsed_ms = (time.perf_counter() - started) * 1000
            with lock:
                latencies.append(elapsed_ms)
                if response.status_code != 200:
                    failures.append(f"status={response.status_code}")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(lambda _: request(), range(requests)))

    p95_ms = statistics.quantiles(latencies, n=20, method="inclusive")[18]
    throughput = requests / (sum(latencies) / 1000 / workers)
    assert not failures
    assert p95_ms < 1000.0
    assert throughput > 50.0

    evidence = {
        "scenario": "api_health_bounded_concurrent_load",
        "requests": requests,
        "workers": workers,
        "failures": len(failures),
        "p95_latency_ms": round(p95_ms, 3),
        "aggregate_worker_normalized_throughput_rps": round(throughput, 3),
        "thresholds": {"p95_latency_ms_lt": 1000.0, "throughput_rps_gt": 50.0},
        "status": "PASS",
    }
    print("LOAD_EVIDENCE|api_health|PASS|" + json.dumps(evidence, sort_keys=True))
    _write_evidence("api_health.json", evidence)
    capsys.readouterr()


def test_scheduler_and_celery_routing_capacity(redis_client: Redis) -> None:
    """High-volume routing preserves tenant fairness and explicit execution queue."""
    scheduler = TenantFairScheduler(
        RedisFairnessStore(redis_client),
        key_prefix="aiep:test:phase-14-13:fair",
    )
    decisions = [scheduler.route("tenant-a") for _ in range(500)]
    newcomer = scheduler.route("tenant-b")
    route = tenant_fair_route("run.execute", ("run-id", "tenant-a"), {}, {}, None)

    assert len(decisions) == 500
    assert decisions[-1].virtual_finish == pytest.approx(500.0)
    assert newcomer.queue_priority == 0
    assert route is not None
    assert route["queue"] == EXECUTION_QUEUE

    evidence = {
        "scenario": "scheduler_and_celery_routing_capacity",
        "reservations": 500,
        "last_virtual_finish": decisions[-1].virtual_finish,
        "newcomer_priority": newcomer.queue_priority,
        "execution_queue": route["queue"],
        "status": "PASS",
    }
    print("LOAD_EVIDENCE|routing|PASS|" + json.dumps(evidence, sort_keys=True))
    _write_evidence("routing.json", evidence)


def test_resource_capacity_and_crash_recovery(redis_client: Redis) -> None:
    """Concurrent admission stays within caps and expired leases recover capacity."""
    limiter = TenantResourceLimiter(
        redis_client,
        {"tenant-a": 4},
        default_limit=2,
        lease_seconds=1,
    )
    lock = threading.Lock()
    active = 0
    maximum = 0
    admitted = 0

    def worker() -> None:
        nonlocal active, maximum, admitted
        lease = limiter.acquire("tenant-a")
        if lease is None:
            return
        with lock:
            active += 1
            admitted += 1
            maximum = max(maximum, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        limiter.release(lease)

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda _: worker(), range(32)))

    assert maximum <= 4
    assert admitted == 4

    abandoned = limiter.acquire("tenant-a")
    assert abandoned is not None
    assert limiter.acquire("tenant-a") is not None
    assert limiter.acquire("tenant-a") is not None
    assert limiter.acquire("tenant-a") is not None
    assert limiter.acquire("tenant-a") is None
    time.sleep(1.1)
    recovered = limiter.acquire("tenant-a")
    assert recovered is not None
    limiter.release(recovered)

    evidence = {
        "scenario": "resource_capacity_and_crash_recovery",
        "configured_limit": 4,
        "concurrent_requests": 32,
        "maximum_active": maximum,
        "admitted_initial": admitted,
        "expired_lease_recovered": True,
        "status": "PASS",
    }
    print("LOAD_EVIDENCE|resource_capacity|PASS|" + json.dumps(evidence, sort_keys=True))
    _write_evidence("resource_capacity.json", evidence)
