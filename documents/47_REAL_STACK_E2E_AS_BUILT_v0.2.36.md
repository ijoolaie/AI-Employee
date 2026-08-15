# Real Stack E2E / Infrastructure Contract — v0.2.36

## Scope
This release closes the infrastructure gap between the Phase 1 code and a reproducible real-stack test environment.

## Included
- PostgreSQL 16 service with healthcheck.
- Redis 7 service with healthcheck.
- FastAPI API container.
- Celery worker container.
- Celery Beat container.
- Backend Dockerfile with production-like dependency installation.
- Fail-closed dependency health endpoint: `GET /health/dependencies`.
- Alembic merge migration that collapses all historical Phase 1 heads into one head.
- `scripts/e2e_stack_verify.py` for real PostgreSQL/Redis/API checks.
- `scripts/run_e2e.sh` for end-to-end stack startup, migration, dependency verification and Celery worker ping.

## Verification performed in this build environment
- Static Python compilation: PASS.
- Migration graph static analysis: PASS; one head (`f6b7c8d9e012`).
- ZIP integrity: PASS after release packaging.
- Real PostgreSQL/Redis/Celery execution: NOT VERIFIED in this environment because Docker is not installed and localhost ports 5432/6379 were closed.

## Required real-environment verification
Run `backend/scripts/run_e2e.sh` on a host with Docker Compose. The script intentionally fails rather than reporting a simulated PASS when PostgreSQL, Redis, API or Celery is unavailable.

## Important semantics
The stack remains at-least-once at the Outbox/Celery boundary. Correctness therefore depends on the workflow idempotency contract already introduced in v0.2.33.
