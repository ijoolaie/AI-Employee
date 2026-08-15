"""Real-stack verification for Phase 1 PostgreSQL/Redis/Celery E2E.

Run this inside the backend container after `docker compose up -d` and after
migrations have been applied. It deliberately fails closed when a dependency
is unavailable; no simulated PASS is produced.
"""
from __future__ import annotations

import asyncio
import os
import sys
from urllib.request import urlopen

import redis
from sqlalchemy import create_engine, text


def main() -> int:
    db_url = os.environ.get("DATABASE_URL_SYNC", "postgresql://aiep:aiep@localhost:5432/aiep")
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    failures: list[str] = []

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        print(f"POSTGRES PASS alembic_version={version}")
    except Exception as exc:
        failures.append(f"POSTGRES: {exc}")

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        if client.ping() is not True:
            raise RuntimeError("PING did not return True")
        print("REDIS PASS ping=true")
    except Exception as exc:
        failures.append(f"REDIS: {exc}")

    try:
        with urlopen("http://localhost:8000/health/dependencies", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            print("API HEALTH PASS")
    except Exception as exc:
        failures.append(f"API HEALTH: {exc}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print("E2E DEPENDENCY CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
