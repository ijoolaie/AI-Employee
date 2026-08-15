# AI Employee Platform v0.9.5 — Sequential Test Execution Plan

**Status tracking**: Mark each item `[x]` when done. Report Failures immediately.

## Phase 0 — Environment (Prerequisite)
- [ ] Docker + Docker Compose available
- [ ] Postgres + Redis up (`cd backend && docker compose up -d`)
- [ ] Backend venv + `pip install -r requirements.txt`
- [ ] `.env` configured (SECRET_KEY, AI_DEFAULT_PROVIDER=lm_studio, CORS_ORIGINS)
- [ ] `alembic upgrade head`
- [ ] Seed scripts run (report, invoice, order, sales employees)
- [ ] API running: `uvicorn app.main:app --reload --port 8000`
- [ ] Celery worker running
- [ ] Frontend: `npm install && npm run dev` → http://localhost:3000
- [ ] LM Studio (optional but recommended) with model loaded
- [ ] Health: `curl http://localhost:8000/health`

## Phase 1 — Frontend Contract & Unit (Automated, no backend required)
- [x] Original contract tests: 49 passed
- [x] Expanded contract tests (v0.9.5 pages + API surface): **105 passed, 0 failed**
- [ ] `npm run test:unit` (vitest) — after npm install completes
- [ ] `npm run lint`
- [ ] Manual visual check of all sidebar links while frontend is running

## Phase 2 — Frontend Live Smoke (Manual / Playwright later)
### 2.1 Auth
- [ ] Register new tenant
- [ ] Login
- [ ] Logout / session expiry redirect
- [ ] `/auth/me` data appears in Settings

### 2.2 Core AI Flow
- [ ] Studio / Employees → New Employee (prompt + tools + autonomy)
- [ ] Start Run from employee detail
- [ ] Run polling → succeeded/failed
- [ ] Trace Explorer shows events
- [ ] AI Chat creates real Run and shows result

### 2.3 Domain pages
- [ ] Dashboard stats load
- [ ] Files upload/list/delete
- [ ] Knowledge index + search
- [ ] Memory create/search/delete
- [ ] Orders list + status update
- [ ] Sales pipeline + deal stage
- [ ] Approvals decide
- [ ] Workflows list/create/builder/schedule
- [ ] Schedules page
- [ ] Billing / Usage
- [ ] Developer (metrics, audit, DLQ replay)
- [ ] API & Integrations / Webhooks pages render
- [ ] Admin (if platform admin): tenants + validation

### 2.4 UX / Edge
- [ ] Empty states with correct icons
- [ ] Mobile navigation
- [ ] Error messages from backend (network / 401 / 403 / 422)
- [ ] Loading spinners

## Phase 3 — Backend Unit + Contract (pytest)
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v --tb=short
```
Key files to keep green:
- test_rbac.py, test_security.py, test_schema_validation.py
- test_ai_providers.py, test_prompt_assembly.py, test_tool_registry.py, test_autonomous_planner.py
- test_report/invoice/order/sales/document_service.py
- test_memory_*, test_rag_*
- test_workflow_*
- test_v03*, test_v04*, test_v046_observability_contract.py, test_v047_billing_contract.py
- test_stripe_service.py, test_usage_service.py, test_external_email_tool.py

Target: all existing tests pass + coverage on services ≥ 80%.

## Phase 4 — Backend Integration / API
- [ ] Auth register/login/refresh/me
- [ ] Tenant isolation (cross-tenant 403/404)
- [ ] Employees CRUD + version publish
- [ ] Runs create + status + trace
- [ ] Files + Knowledge + Memory
- [ ] Workflows full lifecycle
- [ ] Orders / Sales / Invoices
- [ ] Billing plans + subscription (Stripe mock)
- [ ] Approvals + Feedback
- [ ] Admin endpoints
- [ ] DLQ list + replay
- [ ] CORS + security headers + rate limit

Use `httpx.AsyncClient` + pytest fixtures or the OpenAPI `/docs`.

## Phase 5 — Full Stack E2E
- [ ] `python scripts/e2e_stack_verify.py`
- [ ] `python scripts/verify_lm_studio.py`
- [ ] Manual or Playwright: Register → Create Employee → Run → Succeeded
- [ ] Invoice / Order / Sales / Report employee happy paths
- [ ] Workflow trigger → approval → completion
- [ ] Fail-closed cases (no AI key, invalid schema, permission denied)

## Phase 6 — Security & Non-functional
- [ ] RBAC matrix
- [ ] JWT handling
- [ ] Input validation / schema
- [ ] File upload limits & path safety
- [ ] Basic load on /runs and /employees
- [ ] Observability metrics present

## Phase 7 — Regression & CI
- [ ] Add expanded contract test to CI
- [ ] pytest + frontend contract on every PR
- [ ] Document any new endpoint in both backend OpenAPI and frontend `lib/api.ts` + contract test

---

## Current Progress — 2026-08-11

1. Latest reference archive reviewed: `AI_Employee_Platform_Phase_9_Ver.11(1).zip`.
2. Frontend contract suite executed: **105 passed, 0 failed**.
3. Python source compilation executed: **PASS**.
4. Static Alembic graph inspection: **PASS**, exactly one head `0a1b2c3d4e5f`.
5. Real user environment verified Redis/Celery startup and a real `run.execute`: **PASS**, 13.61s, `run_finished`, database `COMMIT`.
6. Real user logs also verified user → tenant → roles → permissions loading during the run.
7. Initial Windows Celery default `prefork` test produced `PermissionError [WinError 5]`; Windows runbook now explicitly recommends `--pool=solo`.
8. Fresh full backend pytest was attempted during package review but could not collect because `asyncpg` was missing from the review environment; this is recorded as **NOT VERIFIED**, not as an application failure.
9. Frontend Vitest, lint and production build remain **NOT VERIFIED** in this audit.
10. Client deployment and production E2E remain **NOT VERIFIED** and are mandatory final gates.

For the complete evidence matrix, see:
`docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md`.
