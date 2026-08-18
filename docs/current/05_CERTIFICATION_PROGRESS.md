# Certification Roadmap Progress

## Status as of 2026-08-19

**Current state: GREEN — full certification stack-smoke gate passed; production-readiness hardening is in progress.**

Latest verified runtime run:
- GitHub Actions Run: `32189879292`
- Repository: `ijoolaie/AI-Employee`
- Result: **SUCCESS**

This document records the implementation/debugging path and certification evidence accumulated through the first fully green end-to-end gate. It is also the working checkpoint for the next production-readiness phase.

## Certification path completed

The current Production Certification workflow successfully passed the following sequence:

1. Frontend installation and contract/unit/build checks
2. Backend dependency installation
3. OCR runtime installation and language verification
4. Python compilation
5. Ruff lint
6. PostgreSQL/Redis service readiness
7. Alembic database migration
8. Backend tests
9. Authentication P0 certification
10. Tenant isolation + RBAC P0 certification
11. Employee -> Run -> AI -> Result product acceptance certification
12. Workflow -> Approval -> Schedule product acceptance certification
13. Orders -> Sales -> Invoice -> Billing product acceptance certification
14. Frontend Playwright E2E against the running stack
15. Stack smoke completion and cleanup

**All of the above passed in Run `32189879292`.**

## Problems found and resolved

### 1. OCR installation hung

Run `32159918638` remained in `Install OCR runtime` for approximately one hour and was cancelled.

Resolution:
- Added an 8-minute timeout to OCR installation.
- Added bounded APT retries and network timeouts.
- Added explicit `tesseract --version` and Farsi language verification.
- Added job-level timeouts for backend/frontend/stack smoke.
- Added workflow concurrency with `cancel-in-progress` to avoid overlapping certification runs.

Result: later runs passed OCR installation normally.

### 2. Sales deal creation returned the wrong HTTP status

The Orders/Sales/Billing certification initially received:

`expected HTTP 201, got 200`

The response payload itself was valid.

Resolution:
- `POST /api/v1/sales/deals` was changed to return `201 Created`.

Result: Sales Deal Create/Link Order passed in subsequent certification.

### 3. Sales stage update raised SQLAlchemy `MissingGreenlet`

After stage update, Pydantic serialization attempted to access `updated_at` while the SQLAlchemy object still required a database load.

Resolution:
- Added `await db.refresh(deal)` before `BusinessDealResponse.model_validate(deal)` in the stage-update endpoint.

Result: Sales Stage passed in subsequent certification.

### 4. Workflow creation returned `401 User not found or inactive`

Registration returned an access token, but the immediately-following authenticated workflow request could race with the transaction commit.

Resolution:
- Added an explicit `await db.commit()` before issuing authentication tokens during registration.
- The token is now issued only after the user/tenant transaction is committed.

Result: Workflow -> Approval -> Schedule certification passed in Run `32189879292`.

## Important commits

The key fixes applied during this certification cycle were:

- `0c36fbaea2a234495ac2c960986369dfc3075918` — bound OCR runtime installation and certification job execution time.
- `78a6aa15e3fc58e487a148640bf187b27912e9c2` — return HTTP 201 for Sales Deal creation.
- `02a127a39b0d0815e78de0f2057b866caac8ae39` — refresh Sales Deal after stage update.
- `e08b95ff6d3ead0f8e4bf11cfd144dd4d0c697e1` — commit user/tenant registration before issuing auth tokens.
- `5dc922a9b5f7b256968f6984f6bdf7cab227ab58` — fail closed on unsafe production URLs/configuration.

## Gate history

| Gate / run | Outcome | Main finding |
|---|---|---|
| `32159918638` | Cancelled | OCR runtime hung for ~1 hour |
| `32171699931` | Failed | Sales Deal Create returned 200 instead of 201 |
| `32188253198` | Failed | Sales Stage raised `MissingGreenlet` |
| `32189037208` | Failed | Workflow Create returned 401 due to registration/auth transaction timing |
| `32189879292` | **PASS** | Full certification stack-smoke green |

## Production-readiness audit checkpoint

The first audit pass was performed after the green runtime checkpoint. One concrete hardening gap was found in application configuration: the production validator already rejected debug mode, weak secrets, disabled rate limiting, and empty CORS, but it did not reject local HTTP origins or localhost service URLs. Those local defaults are appropriate for development/E2E, but unsafe to inherit into a real production environment.

### Hardening applied

Commit `5dc922a9b5f7b256968f6984f6bdf7cab227ab58` strengthens the production configuration guard so that production startup now fails closed when:

- any `CORS_ORIGINS` entry is not HTTPS;
- `FRONTEND_BASE_URL` is not HTTPS;
- `FRONTEND_APP_URL` is not HTTPS;
- database, Redis, Celery broker, or Celery result-backend URLs point to localhost/loopback.

This does not change development or E2E defaults. It makes an accidental production deployment with local/dev endpoints fail at startup instead of silently accepting them.

### Remaining production deployment checks

The repository-level audit is not a production deployment certification. Before a real production release, the deployment environment still needs explicit verification of:

1. HTTPS/reverse proxy and trusted-origin configuration.
2. Production secrets supplied through the deployment secret manager, not repository defaults.
3. Database/Redis/Celery endpoints and network exposure.
4. Worker and beat operation, restart policy, and queue health.
5. Monitoring/logging/OTel exporter configuration and alerting.
6. Storage persistence, backup/restore, and migration/rollback procedure.
7. Production payment/webhook secrets and signature verification where those integrations are enabled.
8. Deployment-specific security review and least-privilege infrastructure configuration.

## Current checkpoint

The repository has a verified green end-to-end certification checkpoint plus an initial production configuration hardening commit. The green runtime evidence covers backend/frontend integration, OCR, lint/compile, migrations/tests, authentication, tenant/RBAC, Employee -> Run -> AI -> Result, Workflow -> Approval -> Schedule, Orders -> Sales -> Invoice -> Billing, and frontend Playwright E2E.

## Next roadmap phase

Do not reopen the already-passed gates unless a later change affects them. Continue from this checkpoint with deployment-specific production readiness rather than adding unrelated features.

1. Run the certification workflow on commit `5dc922a9b5f7b256968f6984f6bdf7cab227ab58`.
2. Verify the production configuration guard with representative production-safe and unsafe settings.
3. Audit deployment manifests/reverse proxy, secrets, worker/beat, observability, storage, and backup/rollback controls.
4. For any failure, diagnose from the first failing gate and fix the underlying contract/runtime issue rather than weakening the certification assertion.
5. Re-run the full certification after each relevant fix.
6. Keep this document updated with new run IDs, root causes, fixes, and the next green checkpoint.

## Operating rule

**A green certification gate is the checkpoint; a failed later gate is the next task. Do not modify already-passing behavior merely to make a later gate pass.**
