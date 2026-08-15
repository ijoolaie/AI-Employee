# Production Readiness Audit v2.0 — Gate 3
## Docker / PostgreSQL / Redis / Celery Integration Certification

**Baseline:** RC8 Production Complete — Audited Gate 2
**Gate:** 3 — Runtime Infrastructure Integration
**Assessment date:** 2026-08-12
**Status:** PARTIAL / BLOCKED BY EXECUTION ENVIRONMENT

## Executive result

The RC8 integration contract is internally consistent and the repository contains a coherent Docker Compose topology for PostgreSQL, Redis, API, Celery worker, Celery beat, and frontend. Static validation passed and the focused integration/observability contract suite passed.

A real containerized certification could not be performed in the current audit environment because the Docker CLI/daemon is unavailable. PostgreSQL and Redis server binaries are also unavailable. Therefore this gate is **not certified** and no claim is made that the containers successfully start, migrate, pass readiness, or execute a real Celery task end-to-end.

## Checks

| Check | Result | Evidence |
|---|---|---|
| Compose YAML parse | PASS | `docker-compose.yml` parsed successfully with PyYAML |
| Service topology | PASS | postgres, redis, api, worker, beat, frontend |
| Build context / Dockerfile existence | PASS | all referenced contexts and Dockerfiles exist |
| PostgreSQL healthcheck contract | PASS | `pg_isready -U aiep -d aiep` |
| Redis healthcheck contract | PASS | `redis-cli ping` |
| API readiness dependency contract | PASS | API depends on healthy PostgreSQL + Redis |
| Worker/beat startup dependency | PASS | worker/beat depend on healthy API + PostgreSQL + Redis |
| Frontend healthcheck contract | PASS | loopback `/login` probe |
| Backend dependency declarations | PASS | asyncpg, redis, celery, psycopg2-binary present |
| Alembic head | PASS | `rc8p0p4pwd` |
| Focused integration contracts | PASS | 12 passed |
| Docker runtime startup | BLOCKED | Docker CLI/daemon unavailable |
| PostgreSQL runtime | BLOCKED | no PostgreSQL server available |
| Redis runtime | BLOCKED | no Redis server available |
| Celery broker/task execution | BLOCKED | requires Docker/Redis + backend runtime |
| Full Docker E2E | BLOCKED | requires container runtime |

## Corrective fix applied in Gate 3

`backend/app/main.py` previously measured the Celery queue using `settings.redis_url` (Redis DB 0), while the Docker Compose contract correctly configures Celery to use `settings.celery_broker_url` (Redis DB 1).

That could silently report an incorrect Celery queue depth even when the broker was healthy.

The metrics probe now uses:

```python
Redis.from_url(settings.celery_broker_url, decode_responses=True)
```

A regression contract test was added to `backend/tests/test_v046_observability_contract.py`.

## Focused verification

```text
12 passed
```

The verified set covers:
- Docker E2E contract
- infrastructure boundaries
- observability metric surface
- OpenTelemetry bootstrap
- Celery/AI/workflow span contracts
- Celery broker queue database selection

## Remaining certification requirements

The following must be executed in a real Docker-enabled staging environment before Gate 3 can become PASS:

1. `docker compose build`
2. `docker compose up -d`
3. PostgreSQL readiness
4. Redis readiness
5. API `/health/dependencies`
6. Alembic upgrade to `rc8p0p4pwd`
7. Celery worker registration
8. Celery task enqueue/consume/result path
9. Celery beat schedule execution
10. API → DB → Redis → Celery integration flow
11. Frontend → API critical flow
12. Docker E2E suite
13. clean shutdown and restart verification

## Certification decision

**Gate 3 = NOT CERTIFIED / BLOCKED**

Reason: infrastructure runtime is unavailable in the audit environment. The repository-side contracts are green, but runtime evidence is mandatory for production certification.
