# Client Handoff & Test Evidence — 1.0.0-rc.8

**Reference archive:** `AI_Employee_Platform_RC8_STAGING_READY_2026-08-15.zip`  
**Audit date:** 2026-08-15  
**Purpose:** deployment handoff and explicit test evidence.

## Current RC8 verification status

The 2026-08-15 RC8 fix pass corrected the API router registration, extended the migration graph to the single head `rc8p0p4pwd`, removed Python bytecode/build artifacts, regenerated `PROJECT_MANIFEST_CURRENT.json`, and re-ran the frontend contract suite.

Current evidence: Python compilation **PASS**; frontend contract suite **141 passed, 0 failed**; migration graph **29 files / one head `rc8p0p4pwd`**. Full backend tests, frontend build/lint/unit tests, browser E2E, Docker E2E and external-provider certification still require their respective runtime environments.

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

The suite covers required pages, navigation, API client methods, types, auth interceptor, admin pages, Orders/Sales pages, Chat/Studio/Dashboard behavior and other frontend contracts.

**Alembic graph — PASS**

The archive contains 29 migration files and static dependency analysis reports exactly one head:

```text
rc8p0p4pwd
```

Do not treat `c2d3e4f5a6b9` as the final head; it is the Business Deals migration.

### B. Real runtime tests performed by the user

**Redis/Celery connection — PASS**

The worker connected to:

```text
redis://localhost:6379/1
```

and reached:

```text
celery@... ready.
```

**Celery task registration — PASS**

The following tasks were loaded:

```text
email.send
outbox.dispatch
run.execute
workflow.approval_expiry
workflow.event_dispatch
workflow.execute
workflow.parallel_branch
workflow.schedule_tick
workflow.timeout_sweep
```

**Real Run execution — PASS**

The user's real environment received:

```text
Task run.execute[...] received
```

and later:

```text
run_finished
COMMIT
Task run.execute[...] succeeded in 13.610000000000582s: None
```

Therefore the observed real path covered queue delivery, worker execution, application/database interaction and transaction completion.

**RBAC/authorization data loading — PASS observed**

During the real run the application successfully queried:
- the user constrained by `users.id` and `users.tenant_id`;
- the user's roles;
- the permissions attached to the role.

No authorization query failure was observed.

### C. Windows Celery issue discovered and documented

The first real worker invocation used the default:

```text
concurrency: 16 (prefork)
```

Several spawned workers failed with:

```text
PermissionError: [WinError 5] Access is denied
```

This is recorded as a **Windows development/runtime issue**, not as an application business-logic failure.

The worker was subsequently restarted and reached `ready`, and the real `run.execute` flow passed.

For Windows development use:

```powershell
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

For production, use Linux where possible and deploy Celery using the server's normal production process model.

## 3. Fresh backend pytest limitation

A fresh review-environment execution of:

```powershell
python -m pytest backend/tests -q --disable-warnings --tb=short
```

could not complete test collection because the review environment did not have `asyncpg`.

Observed root error:

```text
ModuleNotFoundError: No module named 'asyncpg'
```

Collection stopped with 16 import/collection errors.

**Interpretation:** this result is `NOT VERIFIED`, not `FAIL`. The project requirements must first be installed in the project's own virtual environment.

The archive contains 35 backend test modules with 127 top-level `test_*` functions by static inspection.

## 4. Other tests still required before production

| Test | Status |
|---|---|
| Full backend pytest in project `.venv` | NOT VERIFIED |
| Frontend Vitest | NOT VERIFIED |
| Frontend ESLint | NOT VERIFIED |
| Frontend production build | NOT VERIFIED |
| PostgreSQL migration on clean client DB | NOT VERIFIED |
| Auth/register/login on client server | NOT VERIFIED |
| Tenant isolation on client server | NOT VERIFIED |
| Employee → Run → result on client server | NOT VERIFIED |
| Workflow + approval + timeout/retry on client server | NOT VERIFIED |
| Files / Knowledge / Memory smoke | NOT VERIFIED |
| Orders / Sales / Invoice smoke | NOT VERIFIED |
| HTTPS/reverse proxy | NOT VERIFIED |
| Production email | NOT VERIFIED |
| Object storage | NOT VERIFIED |
| Monitoring/alerting | NOT VERIFIED |
| Live payment provider | NOT VERIFIED |

## 5. Historical evidence

Earlier release documents in the archive record successful testing for several completed phases, including:
- Report Employee;
- Document Employee;
- Invoice Employee;
- Order Employee;
- Sales Employee service contracts;
- observability contracts;
- RBAC/security contracts;
- workflow contracts;
- RAG and Memory services;
- LM Studio real-model flows for previously verified employee paths.

Those records remain historical evidence. They should not be described to the client as a fresh production certification for the current server.

## 6. Client deployment sequence

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure production secrets and service URLs.

Then:

```bash
alembic upgrade head
alembic current
alembic heads
alembic check
```

Expected head:

```text
rc8p0p3keys
```

Start API and verify:

```text
/health
/health/dependencies
```

Start Redis-connected Celery worker and, if schedules are enabled, Celery Beat.

### Frontend

```bash
cd frontend
npm install
npm run test
npm run test:unit
npm run build
npm run start
```

Put the frontend behind the client's HTTPS reverse proxy.

## 7. Production secrets

The client must provide/configure:
- strong `SECRET_KEY`;
- PostgreSQL URL;
- Redis URL;
- CORS origins;
- AI provider settings;
- SMTP/email settings if email features are enabled;
- object storage settings if used;
- Stripe/payment settings only if billing is enabled;
- monitoring/telemetry settings.

Never send real secrets inside the ZIP.

## 8. Release classification

**CLIENT HANDOFF:** YES  
**DEPLOYMENT CANDIDATE:** YES  
**PRODUCTION CERTIFIED:** NO

Production certification must be granted only after the client's actual server passes the remaining deployment-specific gates.
