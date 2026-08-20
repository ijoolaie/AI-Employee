# AI Employee Platform — Clean Implementation Master Guide
## Release: 1.0.0-rc.8

This release is a cleaned implementation baseline assembled from the supplied `AI_Employee_Platform_RC8_STAGING_READY_2026-08-15.zip`.

**Important:** this is a release candidate, not a claim of production certification. The correct workflow is: install → migrate → static checks → backend tests → frontend tests/build → live smoke → E2E → only then production deployment.

## 1. What is included

### Backend
FastAPI, PostgreSQL/SQLAlchemy async, Alembic, Redis, Celery/Beat, JWT authentication, multi-tenancy/RBAC, files, employees/runs, AI gateway, memory, RAG/knowledge, workflows, approvals, schedules/events, billing, invoices, orders, sales/deals, feedback, developer/admin operations, metrics and telemetry.

### Frontend
Next.js App Router + React + TypeScript. Panels/routes are organized into:
- Auth
- Customer dashboard
- Employees / Employee detail
- Runs / Run detail
- Files
- Knowledge
- Memory
- Chat
- Studio
- Workflows / Builder / Schedules
- Approvals
- Orders
- Sales
- Billing / Usage
- Developer / Traces / API keys / Webhooks
- Admin / Tenants / Validation

### Documents
The original historical documents are retained. `docs/current/` is the authoritative implementation guide for this release. Older release notes are history, not current instructions.

## 2. Architecture

```text
Browser
  │
  ▼
Next.js Frontend :3000
  │ HTTP/JSON
  ▼
FastAPI API :8000
  ├── PostgreSQL 16  ← durable application state
  ├── Redis           ← cache/rate-limit + Celery broker/result
  ├── Celery Worker   ← asynchronous Runs / background work
  ├── Celery Beat     ← scheduled workflows/tasks
  └── AI Gateway
       ├── LM Studio (local development)
       └── optional Anthropic / other provider adapters
```

The API is the source of truth for authorization and tenant isolation. The browser must never be trusted to enforce permissions.

## 3. Correct build order

Do not implement everything simultaneously.

1. Infrastructure
2. Backend configuration
3. Database migration
4. Backend startup
5. Authentication and tenant isolation
6. Employees
7. Runs + Celery
8. AI Gateway / LM Studio
9. Files
10. Knowledge + Memory
11. Workflows + approvals + schedules
12. Business modules: orders → sales/deals → invoices → billing
13. Developer/Admin/Observability
14. Frontend contract tests
15. Frontend live smoke
16. Full E2E
17. Production hardening

## RC8 authoritative release metadata

For this exact RC8 archive, the authoritative Alembic head is **`rc8p0p4pwd`**.
The older `0a1b2c3d4e5f` and `rc8p0p3keys` references retained in historical release notes must not be used as the current head.

The RC8 release also includes API key management, tenant administration, provider administration/readiness, customer channels, commerce, and the corresponding frontend contract coverage.

## 4. Database rule

The RC8 archive contains the complete migration graph and has exactly one Alembic head: **`rc8p0p4pwd`**.

The final migration is `backend/alembic/versions/rc8_p0_p4_password_recovery.py`, whose single parent is `rc8p0p3keys`. The previously documented `0a1b2c3d4e5f` and `rc8p0p3keys` values are historical intermediate revisions, not the current RC8 head.

Do **not** use `alembic stamp` to hide a mismatch. Run:

```powershell
cd backend
alembic upgrade head
alembic current
alembic heads
alembic check
```

The expected head for this archive is:

```text
rc8p0p4pwd (head)
No new upgrade operations detected.
```

If the database contains an unknown schema state, stop and inspect before applying migrations.

## 5. Backend implementation

### 5.1 Create environment

```powershell
cd backend
Copy-Item .env.example .env
```

Set a real random `SECRET_KEY` for anything beyond local development.

### 5.2 Start infrastructure

```powershell
docker compose up -d postgres redis
docker compose ps
```

### 5.3 Install backend

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5.4 Migrate

```powershell
alembic upgrade head
alembic current
alembic heads
alembic check
```

### 5.5 Run API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- `/docs`
- `/redoc`
- `/health`
- `/health/dependencies`

### 5.6 Run worker

In another terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

For scheduled jobs, a third terminal:

```powershell
python -m celery -A app.workers.celery_app beat -l info
```

## 6. Frontend implementation

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run test
npm run test:unit
npm run dev
```

Open `http://localhost:3000`.

For a production-style local build:

```powershell
npm run build
npm run start
```

## 7. First real user flow

1. Register a tenant/user.
2. Log in.
3. Confirm Dashboard loads.
4. Create an Employee.
5. Give it a simple prompt.
6. Start a Run.
7. Confirm the Run moves through pending/queued/running to succeeded or failed.
8. Open the Run detail and inspect output/trace.
9. Upload a small file.
10. Create/search a knowledge item if the AI/embedding stack is configured.
11. Create a workflow only after the basic Run flow is green.
12. Add approval/scheduling only after the workflow itself is green.

## 8. AI configuration

For local development:
- Start LM Studio.
- Load the configured chat model.
- Start its OpenAI-compatible server.
- Keep `AI_DEFAULT_PROVIDER=lm_studio`.
- Confirm the configured model name matches LM Studio exactly.

Do not make billing/provider credentials a prerequisite for testing local AI.

## 9. Test gates

### Gate A — static
```powershell
python -m compileall app
alembic check
```

### Gate B — backend
```powershell
pytest tests -v --tb=short
```

### Gate C — frontend
```powershell
npm run test
npm run test:unit
npm run build
```

### Gate D — live
- health
- auth
- tenant isolation
- employee
- run
- AI
- files
- workflow
- approval
- billing/business modules
- admin/developer

### Gate E — release
Only package the build after all previous gates pass.

## 10. What not to do

- Do not manually edit production tables to make Alembic happy.
- Do not `alembic stamp head` unless the database has independently been proven to match the complete schema.
- Do not put `.env`, API keys, Stripe secrets or SMTP credentials in Git/ZIP.
- Do not call the AI provider directly from frontend code.
- Do not bypass backend tenant/RBAC checks because a page is hidden in the UI.
- Do not introduce a new migration for an already-existing schema change without first reproducing the mismatch.

## 11. Definition of Done

A module is done only when:
- backend schema exists and migration is reversible where practical;
- service layer works;
- API contract is defined;
- authorization/tenant isolation is tested;
- frontend page works against the real API;
- loading/empty/error/success states exist;
- automated tests pass;
- live smoke test passes;
- documentation explains how to use it.



## 11. Client handoff status — 2026-08-11

This archive is the current source reference for client deployment.

### Verified in the current handoff review
- Python source compilation: **PASS** (`python -m compileall backend/app backend/scripts`).
- Frontend contract suite: **PASS — 105 passed, 0 failed**.
- Static Alembic graph inspection: **PASS — exactly one head, `rc8p0p4pwd`**.
- Redis connectivity / Celery worker startup: **PASS** in the user's real local environment.
- Registered Celery task set loaded successfully.
- A real `run.execute` task completed successfully in the user's environment in **13.61 seconds**, ending with `run_finished` and database `COMMIT`.
- User/role/permission SQL loading was observed successfully during that real run.

### Known test limitation
A fresh full `pytest backend/tests` execution was attempted during package review, but the review environment did not have the project's `asyncpg` dependency installed. Collection stopped with **16 import/collection errors**, all rooted in `ModuleNotFoundError: asyncpg`. This is **not recorded as an application test failure**; it is an incomplete test-environment prerequisite.

### Not yet release-certified from this archive
- Frontend `npm run test:unit`.
- Frontend `npm run lint`.
- Frontend production `npm run build`.
- Fresh full backend pytest run inside the project's intended `.venv` with all requirements installed.
- Fresh production PostgreSQL/Redis/Celery/AI end-to-end run on the client's server.
- Production HTTPS, reverse proxy, email, object storage, monitoring and secrets configuration.
- Live payment provider verification.

See `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` for the complete evidence matrix.

## RC3 — Customer Operations Surface

RC3 adds the customer-operations layer: persistent Customer CRM, WhatsApp channel foundation, unified human handoff, and a shared inbox transcript/reply experience. These capabilities are intentionally surfaced in the tenant navigation and customer-channel management UI.

**Cross-surface acceptance rule:** every new backend option must update the related Business Dashboard, AI Workspace, Customer Channels, Inbox/CRM, onboarding checklist, and platform/admin surfaces where applicable. A backend-only option is not considered complete.
