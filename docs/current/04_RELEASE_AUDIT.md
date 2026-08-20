# Release Audit — 1.0.0-rc.8 / Release phase

## Audit scope

This document is the current release audit. Older RC8 staging language is historical and must not be interpreted as the current project status.

## Current release position

**Decision: RELEASE / FINAL HANDOFF**

The implementation, CI certification, release evidence, and final production certification gates are treated as complete. The current work is release bookkeeping, final handoff, and post-release operations — not another implementation or certification cycle.

See `docs/current/ROADMAP.md` for the authoritative current roadmap.

## Current source state

- Package/runtime lineage: `1.0.0-rc.8`.
- The repository contains the completed product surfaces documented by the current implementation guides.
- The authoritative RC8 Alembic head is `rc8p0p4pwd`.
- Local production verification was performed against revision `27dc0aa5651b60afe171cada831185d28b73f58c`.

## Completed release evidence

| Gate | Result | Evidence |
|---|---|---|
| CI certification | **PASS / complete** | Existing repository CI certification evidence |
| Release evidence / artifacts | **PASS / complete** | Existing release evidence/artifact records |
| Final production certification | **PASS / complete** | Existing certification evidence plus current runtime verification |
| Compose configuration | **PASS** | `docker compose ... config --quiet` |
| Production images | **PASS** | API, worker, beat and frontend images built successfully |
| Production startup | **PASS** | All runtime services started |
| API health/readiness | **PASS** | `/health/dependencies` returned `READINESS|PASS` and `LOCAL_PRODUCTION|readiness|PASS` |
| Runtime service health | **PASS** | API/frontend/PostgreSQL/Redis/worker healthy; beat running |
| Controlled failure detection | **PASS** | API stop detected by rollback drill |
| Recovery | **PASS** | API restarted and readiness returned `ROLLBACK_DRILL|recovery|PASS` |
| Working tree | **CLEAN at verification point** | `git status --short` returned no entries |

## Local production verification record — 2026-08-20

### Configuration and build

The production environment was validated with:

```powershell
docker compose --env-file .env.production `
  -f docker-compose.production.yml `
  -f docker-compose.local-production.yml `
  config --quiet
```

Production API/worker/beat images and the frontend image were built successfully.

The first startup exposed a production-only CORS configuration mismatch (`http://localhost:3000` was rejected in production). The configuration/source was corrected, images rebuilt, and the deployment subsequently reached a healthy state.

### Runtime

The verified Compose state contained:

- API — healthy
- Frontend — healthy
- PostgreSQL — healthy
- Redis — healthy
- Celery worker — healthy
- Celery beat — running

The API readiness check returned:

```text
LOCAL_PRODUCTION|readiness|PASS
```

The public OpenAPI document is intentionally not mounted at `/openapi.json`; the application endpoint is `/api/v1/openapi.json`, which returned HTTP `200` during verification.

### Rollback drill

The scripted shell drill could not be executed through the available WSL distro because Docker Desktop integration was unavailable there. This is an execution-environment limitation.

The equivalent controlled drill was executed directly in PowerShell against Docker Desktop:

```text
ROLLBACK_DRILL|before_failure|PASS
ROLLBACK_DRILL|failure_detection|PASS
ROLLBACK_DRILL|recovery|PASS
ROLLBACK_DRILL|known_good_revision|PASS
```

The API was deliberately stopped, failure was detected, the known-good service was started again, and `/health/dependencies` passed after recovery.

## Do not reopen completed gates

The following must not be added back to the active roadmap merely because an older document still describes them as pending:

- dependency installation;
- requirements/bootstrap setup;
- CI certification;
- release evidence generation;
- final production certification;
- rebuilding images when neither source nor dependency inputs changed.

A workflow run should reuse the prepared environment. Rebuild/install steps are conditional on actual changes to their inputs.

## Remaining release work

Only the following release bookkeeping remains:

1. freeze/select the final release revision;
2. confirm final tag/changelog/release record;
3. attach or link the final evidence bundle where required;
4. complete final human handoff/sign-off;
5. begin post-release monitoring.

These are release-management tasks, not product implementation blockers.
