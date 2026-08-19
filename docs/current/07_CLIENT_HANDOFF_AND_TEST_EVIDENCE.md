# Client Handoff & Test Evidence — 1.0.0-rc.8

**Reference archive:** `AI_Employee_Platform_RC8_STAGING_READY_2026-08-15.zip`  
**Audit date:** 2026-08-15  
**Purpose:** deployment handoff and explicit test evidence.

## Current RC8 verification status

The 2026-08-15 RC8 fix pass corrected the API router registration, extended the migration graph to the single head `rc8p0p4pwd`, removed Python bytecode/build artifacts, regenerated `PROJECT_MANIFEST_CURRENT.json`, and re-ran the frontend contract suite.

Current evidence: Python compilation **PASS**; frontend contract suite **141 passed, 0 failed**; migration graph **29 files / one head `rc8p0p4pwd`**. Full backend tests, frontend build/lint/unit tests, browser E2E, Docker E2E and external-provider certification require their respective runtime environments.

## 1. What the client is receiving

The archive contains:
- FastAPI backend;
- PostgreSQL/SQLAlchemy/Alembic database layer;
- Redis + Celery background execution;
- AI provider gateway;
- Employees / Runs / Traces;
- Files / Knowledge / Memory;
- Workflows / Approvals / Schedules / Events;
- Billing / Invoices / Orders / Sales;
- Developer/Admin operations;
- Next.js frontend;
- migrations, tests and implementation documentation.

No real `.env` secrets should be included in the deployment package.

## 2. Test evidence

### A. Static/source checks

**Python compilation — PASS**

Command:

```powershell
python -m compileall backend/app backend/scripts
```

Result: exit code `0`.

**Frontend contract suite — PASS**

Command:

```powershell
node frontend/scripts/test-frontend-contract.mjs
```

Result:

```text
Result: 141 passed, 0 failed
```

**Alembic graph — PASS**

The archive contains 29 migration files and static dependency analysis reports exactly one head:

```text
rc8p0p4pwd
```

### B. Real runtime tests performed by the user

**Redis/Celery connection — PASS**

The worker connected to `redis://localhost:6379/1` and reached `celery@... ready.`

**Celery task registration — PASS**

Registered tasks include `run.execute`, workflow execution/scheduling/approval tasks, `email.send`, and `outbox.dispatch`.

**Real Run execution — PASS**

A real `run.execute` completed successfully in 13.61s, ending with `run_finished` and database `COMMIT`.

**RBAC/authorization data loading — PASS observed**

The real run successfully loaded the user, tenant-constrained roles and permissions.

### C. Windows Celery issue discovered and documented

The first Windows worker invocation using the default prefork pool produced `PermissionError: [WinError 5] Access is denied`. The worker was subsequently restarted with the supported Windows configuration and reached `ready`; the real `run.execute` flow passed.

For Windows development use:

```powershell
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

For production, use Linux where possible and deploy Celery using the server's normal production process model.

## 3. Fresh backend pytest limitation

A fresh review-environment execution of the backend pytest suite could not complete collection because the review environment did not have `asyncpg` installed. This is recorded as **NOT VERIFIED**, not as an application test failure. The project's complete dependency set must be installed before judging the suite.

## 4. Current certification matrix

The authoritative CI workflow is `.github/workflows/production-certification.yml`. It currently runs, in sequence:

1. backend compile/lint/migration/tests;
2. frontend contract/unit/build;
3. real Docker stack startup and readiness;
4. Auth P0;
5. Tenant Isolation + RBAC P0;
6. Employee → Run → AI → Result Product Acceptance;
7. Workflow → Approval → Schedule Product Acceptance;
8. Orders → Sales → Invoice → Billing Product Acceptance;
9. frontend Playwright E2E.

The following areas remain separate release gates and must not be inferred as certified merely because the main stack-smoke passes:

| Gate | Status |
|---|---|
| Files / Knowledge / Memory fresh live smoke | NOT VERIFIED |
| Developer / Admin / API-key operations fresh live smoke | NOT VERIFIED |
| Observability / traces / telemetry fresh live smoke | NOT VERIFIED |
| Full frontend Playwright E2E | PENDING fresh successful certification run |
| Clean production database migration | NOT VERIFIED on client environment |
| HTTPS / reverse proxy | NOT VERIFIED |
| Production secrets/configuration | NOT VERIFIED |
| Email / SMTP | NOT VERIFIED |
| Object storage | NOT VERIFIED |
| Monitoring / alerting | NOT VERIFIED |
| Backup / restore / recovery | NOT VERIFIED |
| Live payment provider | NOT VERIFIED |
| Production security certification | NOT CLAIMED |

Historical tests for these areas are retained as historical evidence only; they are not silently reclassified as fresh production certification.

## 5. Deployment sequence

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure production secrets and service URLs, then:

```bash
alembic upgrade head
alembic current
alembic heads
alembic check
```

Expected current RC8 head:

```text
rc8p0p4pwd (head)
```

Start API and verify `/health` and `/health/dependencies`, then start Redis-connected Celery Worker and Beat where schedules are enabled.

### Frontend

```bash
cd frontend
npm ci
npm run test
npm run test:unit
npm run build
npm run start
```

Put the frontend behind the client's HTTPS reverse proxy.

## 6. Production secrets

The client must provide/configure:
- strong `SECRET_KEY`;
- PostgreSQL URL;
- Redis URL;
- CORS origins;
- AI provider settings;
- SMTP/email settings if enabled;
- object storage settings if used;
- Stripe/payment settings only if billing is enabled;
- monitoring/telemetry settings.

Never send real secrets inside the ZIP.

## 7. Release classification

**CLIENT HANDOFF:** YES  
**DEPLOYMENT CANDIDATE:** YES  
**PRODUCTION CERTIFIED:** NO

Production certification must be granted only after the remaining live/runtime and deployment-specific gates pass with fresh evidence.
