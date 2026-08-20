# AI Employee Platform — Master Guide
## Release / Final Handoff Phase

This document is the current operational guide. The repository is past the implementation-first roadmap: core implementation, CI certification, release evidence, and final production certification are already complete. The active phase is **Release → Final Handoff → Post-release Operations**.

For the current status and remaining work, see `docs/current/ROADMAP.md`.

## 1. Product baseline

The platform includes the completed backend, frontend, database migrations, asynchronous workers, AI gateway, authentication/multi-tenancy/RBAC, files, employees/runs, memory/RAG/knowledge, workflows/approvals/schedules, business modules, developer/admin operations, observability, and the documented customer-operations surfaces.

## 2. Release baseline

- Current repository lineage: RC8 / `1.0.0-rc.8`.
- Authoritative Alembic head: `rc8p0p4pwd`.
- Current verified local production revision: `27dc0aa5651b60afe171cada831185d28b73f58c`.
- CI certification: **complete**.
- Release evidence/artifacts: **complete**.
- Final production certification: **complete**.
- Local production deployment/readiness: **verified**.
- Rollback/recovery drill: **verified**.

## 3. Release verification already completed

The following evidence is accepted and should not be repeated unless the relevant inputs change:

- Compose configuration validation;
- container image builds;
- production service startup;
- API/frontend/PostgreSQL/Redis/worker/beat health;
- `/health/dependencies` readiness;
- controlled API failure detection;
- API recovery to the known-good service;
- existing CI/release/certification evidence.

The local verification record is maintained in `docs/current/04_RELEASE_AUDIT.md`.

## 4. One-time setup vs per-run execution

The workflow execution model is intentionally incremental.

### One-time / change-triggered work

Run these only on a new environment or when their inputs change:

- install Python/Node dependencies;
- provision PostgreSQL/Redis;
- run migrations when migration inputs changed;
- build images when source or dependency inputs changed;
- establish or refresh CI/release artifacts when the release candidate changes.

### Every workflow/run

Reuse the existing environment and perform only the work needed by the requested operation:

1. confirm services are available;
2. execute the workflow/run;
3. observe status/logs/results;
4. perform the relevant business acceptance checks;
5. record failures or release-impacting regressions.

Do **not** recreate dependency environments or reinstall requirements on every run.

## 5. Current production-style local stack

The verified local production Compose stack contains:

```text
Next.js frontend :3000
        │
        ▼
FastAPI API :8000
   ├── PostgreSQL 16
   ├── Redis 7
   ├── Celery worker
   └── Celery beat
```

The API is the source of truth for authorization and tenant isolation.

## 6. Health and readiness

Use the application readiness endpoint rather than assuming container startup means the application is ready:

```powershell
docker compose @compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('READINESS|PASS')"
```

The OpenAPI document is exposed at `/api/v1/openapi.json` in this deployment.

## 7. Rollback/recovery

The accepted local recovery drill is:

1. verify the known-good revision;
2. verify readiness;
3. stop API as a controlled failure;
4. verify failure detection;
5. restart API;
6. verify readiness/recovery.

The 2026-08-20 PowerShell drill passed all stages. The WSL shell wrapper was not used because Docker was unavailable in that WSL distro.

## 8. Release checklist

- [x] Implementation baseline complete.
- [x] CI certification complete.
- [x] Release evidence/artifacts complete.
- [x] Final production certification complete.
- [x] Local production deployment verified.
- [x] Runtime readiness verified.
- [x] Rollback/recovery verified.
- [ ] Freeze final release revision/tag.
- [ ] Confirm final changelog/release record.
- [ ] Attach/confirm final evidence bundle.
- [ ] Human release handoff/sign-off.
- [ ] Begin post-release monitoring.

## 9. Do not regress the roadmap

Historical implementation instructions in older documents may describe setup, certification, or test gates as pending. Treat those as historical evidence unless `docs/current/ROADMAP.md` explicitly reopens a gate because a relevant input changed.

Do not:

- rerun dependency installation for every workflow execution;
- rebuild unchanged images for every run;
- repeat CI certification merely because a workflow is executed locally;
- recreate release artifacts when the release baseline has not changed;
- treat an expected `404` at `/openapi.json` as an API failure when `/api/v1/openapi.json` is the configured endpoint.
