# Release Audit — 1.0.0-rc.8 / RC8 staging

## Audit scope

This audit applies to the archive supplied as the latest project reference:

`AI_Employee_Platform_RC8_STAGING_READY_2026-08-15.zip`

The archive contains the current backend, frontend, migrations, tests and historical documentation.

## Current source state

- Package/runtime target: `1.0.0-rc.8`
- Phase 9 Sales Employee: implemented.
- Phase 9 Orders/Sales frontend pages: present.
- Workflow execution fix from Phase 9 Ver.11: documented in `CHANGELOG.md`.
- The current migration graph contains **29 migration files**.
- Static graph inspection reports exactly **one Alembic head: `rc8p0p4pwd`**.
- `rc8_p0_p4_password_recovery.py` is the final RC8 migration and its single parent is `rc8p0p3keys`.

## Test and verification evidence

| Test / check | Result | Evidence |
|---|---|---|
| Python source compilation | **PASS** | `python -m compileall backend/app backend/scripts` |
| Frontend contract tests | **PASS** | `node frontend/scripts/test-frontend-contract.mjs` → **141 passed, 0 failed** |
| Static Alembic head analysis | **PASS** | Exactly one head: `rc8p0p4pwd` |
| Celery task registration | **PASS** | User real worker log lists 9 registered tasks |
| Redis broker connection | **PASS** | User real worker log: connected to `redis://localhost:6379/1` |
| Celery worker readiness | **PASS** | User real log reached `celery@... ready.` |
| Real `run.execute` | **PASS** | User real run completed in **13.61s** |
| SQLAlchemy user/tenant authorization lookup | **PASS observed** | User real log loaded user, roles and permissions |
| Transaction commit after run | **PASS observed** | User real log: `run_finished` followed by `COMMIT` |
| Windows Celery default prefork | **FAIL / known environment issue** | Initial real run produced `PermissionError [WinError 5]` in billiard SpawnPoolWorker |
| Windows Celery `--pool=solo` | **RECOMMENDED** | Existing Windows runbook |
| Full backend pytest in fresh review environment | **NOT VERIFIED** | Collection blocked by missing `asyncpg`; 16 collection errors |
| Frontend Vitest unit suite | **NOT VERIFIED** | Dependencies/build environment not installed during this audit |
| Frontend lint | **NOT VERIFIED** | Not run in this audit |
| Frontend production build | **NOT VERIFIED** | Not run in this audit |
| Client-server production E2E | **NOT VERIFIED** | Must be run after deployment |
| Live payment provider | **NOT VERIFIED** | No live provider configuration |
| Production security certification | **NOT CLAIMED** | Requires deployment-specific audit |

### Historical test evidence retained from earlier release work

The package's historical documentation records additional successful checks, including:
- earlier backend unit/contract suites;
- observability, RBAC, security, workflow, RAG, memory, billing and service-level tests;
- Report Employee, Document Employee, Order Employee and Invoice Employee verification;
- LM Studio real-model verification for previously completed employee flows;
- frontend contract expansion to 105 tests.

These historical results are preserved as evidence but are **not silently reclassified as a fresh full-suite run for this exact archive**.

## Important runtime metadata discrepancy

The package declares `1.0.0-rc.1` in the main application metadata, but the health endpoint implementation currently returns `1.0.0-rc.8` in its response payload.

This is a documentation/release consistency issue that should be corrected in source code before presenting the package as a formally version-aligned production release.

## Production deployment decision

**Decision: NO-GO / STAGING VERIFICATION REQUIRED**

The archive has been corrected for known release-integrity issues, but it must not be treated as production-certified until the runtime gates below execute successfully.

**Decision is NOT: production certified.**

The client must complete:
1. dependency installation;
2. PostgreSQL and Redis provisioning;
3. `alembic upgrade head`;
4. backend health checks;
5. Celery worker/beat startup;
6. frontend dependency installation and production build;
7. real authentication and tenant-isolation smoke tests;
8. real Employee → Run → result flow;
9. business module smoke tests;
10. HTTPS/reverse-proxy configuration;
11. secrets and environment configuration;
12. monitoring/logging setup.
