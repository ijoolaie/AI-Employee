# AI Employee Platform — Backend

v0.2.33-LMSTUDIO — Phase 1 Core RBAC enforcement + local LM Studio AI provider per project docs v1.2 (`21_CrossCutting_Additions_v1.0`),
following the roadmap build order A→B→C→D→E: scaffold → Identity/Tenant/Auth
→ Files/Queue → AI Gateway skeleton → Employee/Run skeleton.

## Stack

- FastAPI + SQLAlchemy 2 (async) + PostgreSQL + Redis + Celery
- JWT Auth, Multi-Tenant, RBAC foundation
- Structured JSON logging + request correlation (telemetry baseline)
- Audit Log (global, independent Core module)
- AI Gateway (provider-agnostic interface; LM Studio is the default local provider,
  Anthropic remains optional)

## What's new in v0.2.0

Per the architecture review recorded in docs v1.2, the following were
added as **non-removable Phase 1 requirements** (not deferred):

- **Audit Log** (`app/models/audit_log.py`, `app/services/audit_service.py`)
  — every sensitive action (auth, Employee/Run lifecycle, AI provider calls,
  file uploads) is recorded, including on failure paths.
- **Telemetry baseline** (`app/core/logging.py`, `app/core/middleware.py`)
  — JSON structured logs, `X-Request-ID` propagated through the whole
  request and into Audit Log / AI Gateway records.
- **Versioning** — `Employee` / `EmployeeVersion` (`app/models/employee.py`):
  every meaningful change publishes a new immutable version; `Run` locks
  to one specific `employee_version_id`, never "current", so historical
  Runs stay reproducible (Replay).

Also added, per the same review, as Phase 2-scoped groundwork built now
because the data model needs to exist before the UI does:

- **AI Gateway** (`app/ai/`) — single entry point for model calls; records
  latency/tokens/cost for every call in `ai_provider_calls` (the data
  source for the future Cost Dashboard).
- **Files** (`app/models/file.py`, `app/services/storage.py`) — tenant-
  scoped upload/list/soft-delete, local-disk backend now, swappable for
  S3-compatible storage later.
- **Employee / Run** (`app/models/employee.py`, `app/models/run.py`,
  `app/services/employee_service.py`, `app/services/run_service.py`) —
  the runtime model from `11_Employee_Framework` §5: create → validate
  input → execute via AI Gateway → store output/cost/trace.

Deferred / rejected in this pass (see `21_CrossCutting_Additions_v1.0` for
rationale): Agent Runtime (Planner→Executor), Feature Flags, Plugin Loader,
Event Bus, separate Job Orchestration.

## Quick start

```bash
# Start infrastructure
docker compose up -d   # postgres + redis

# Install deps (venv recommended)
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # for local development keep LM Studio as the default provider

# Migrations
alembic upgrade head

# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run the async worker (separate process) — required for Runs to execute
celery -A app.workers.celery_app worker -l info
# Windows development: add --pool=solo
```

With the default LM Studio configuration, no Anthropic API key is required. If `AI_DEFAULT_PROVIDER=anthropic` is selected without a key, Runs fail at execution with a clear error and that failure is still fully recorded in `runs.error`, `audit_logs`, and `ai_provider_calls`.

## Current endpoints

**Auth**
- `POST /api/v1/auth/register` — create tenant + first user
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET  /api/v1/auth/me`

**Files**
- `POST /api/v1/files` — upload
- `GET  /api/v1/files` / `GET /api/v1/files/{id}` / `DELETE /api/v1/files/{id}`

**Employees**
- `POST /api/v1/employees` — create Custom Employee (v1 draft, `is_current` version 1)
- `GET  /api/v1/employees` / `GET /api/v1/employees/{id}`
- `POST /api/v1/employees/{id}/versions` — publish a new version

**Runs**
- `POST /api/v1/runs` — create + enqueue execution
- `GET  /api/v1/runs` / `GET /api/v1/runs/{id}`

All endpoints except `/health` and `auth/register|login|refresh` require
`Authorization: Bearer <access_token>` and are scoped to the caller's tenant.

## Verified in this build

- `alembic upgrade head` applied cleanly against a real PostgreSQL 16
  instance — 13 tables created.
- End-to-end smoke test: register → login → create Employee → create Run
  → Celery worker executes it → AI Gateway call attempted → failure (no
  API key in this env) correctly recorded on the Run **and** in
  `audit_logs` **and** `ai_provider_calls`.
- `pytest` — existing unit tests pass.

## Structure

See documentation: `04_Architecture_v1.0`, `07_Backend_v1.0`,
`10_AI_Core_v1.1`, `11_Employee_Framework_v1.0`, `05_Database_v1.0`, and
`21_CrossCutting_Additions_v1.0` for the decisions behind this build.


## Windows notes

- Create venv: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
- Alembic needs a sync driver: `pip install psycopg2-binary` (also listed in requirements)
- Celery on Windows: always use solo pool:

```bash
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

- If `alembic` reports `Can't locate revision identified by '...'`, reset local DB:

```bash
docker compose down -v
docker compose up -d
python -m alembic upgrade head
```

- PowerShell: use `Invoke-RestMethod` (or `curl.exe`) — the `curl` alias is not real curl.


## RBAC (Phase 1)

The first user created for a tenant is assigned the tenant-scoped `Admin` role.
Core permissions are stored as global Permission records and attached to that
role. Protected Employee, Run, and File endpoints enforce permissions through
FastAPI dependencies; a role from another tenant can never satisfy a permission
check. The existing `is_superuser` flag remains a compatibility full-access
path for the current v1 identity model.


## Autonomous Employee Runtime (v0.9.3)

The v0.9.3 runtime connects the existing Memory and Tool subsystems to an opt-in autonomous planning layer. No provider-specific code is added: the planner uses the same AI Gateway and therefore works with LM Studio.

EmployeeVersion rules can enable it:

```json
{
  "autonomy": {
    "enabled": true,
    "max_steps": 6,
    "require_plan": true
  },
  "memory": {
    "enabled": true,
    "auto_extract": true,
    "query_fields": ["message"]
  }
}
```

Runtime flow:

```text
Run
 -> RAG + Memory retrieval
 -> Autonomous Planner (opt-in)
 -> Prompt Assembly with plan
 -> LM Studio
 -> Tool Registry / approvals / RBAC
 -> Verification via normal model/tool loop
 -> Memory extraction
```

The planner never executes a Tool directly. It can only suggest tools that are already explicitly allowed by the immutable EmployeeVersion. Actual execution remains inside `app.ai.tool_registry`, so existing tenant isolation, permissions, validation, audit logging, and Human Approval behavior remain the security boundary.

`require_plan=true` fails closed when planning fails. Set it to `false` if the Employee should fall back to the normal non-planned tool loop.

## Local AI with LM Studio

The default development AI provider is LM Studio. Start the LM Studio local server and load `google/gemma-4-e4b`. The backend expects the OpenAI-compatible API at `http://127.0.0.1:1234/v1`.

Relevant environment variables:

```env
AI_DEFAULT_PROVIDER=lm_studio
AI_DEFAULT_MODEL=google/gemma-4-e4b
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=
```

No Anthropic API key is required for local development. Anthropic remains available by setting `AI_DEFAULT_PROVIDER=anthropic` and configuring `ANTHROPIC_API_KEY`.


## As-Built documentation rule

The package distinguishes **Planned**, **As-Built**, and **Verified**. The long-term product plan remains authoritative for direction, while `documents/00_AS_BUILT_BASELINE_v0.2.14_LMSTUDIO.md` is authoritative for the current code/package state. v0.2.13 adds a provider-neutral Prompt + Context Assembly layer on top of the v0.2.12 Draft 2020-12 JSON Schema validation for Run input/output contracts and Employee schema definitions. The real `.env` is never shipped; only `.env.example` is included.

### Windows Celery / asyncpg note

Celery Run tasks use a worker-local SQLAlchemy async engine with `NullPool` so asyncpg connections are not reused across the event loops created by `asyncio.run()`. This specifically addresses the Windows Proactor `NoneType.send` failure observed during the first LM Studio E2E attempt.


## v0.2.14 — Validation Layer

Employee input/output contracts use Draft 2020-12 JSON Schema validation with enabled format assertions, bounded structured validation errors, local JSON Pointer references, and rejection of external `$ref`/`$dynamicRef` resources. Schema validation is provider-agnostic and executes before provider calls for input and after provider execution for output.

### Usage reporting (v0.2.18)

`GET /api/v1/usage/summary` provides tenant-scoped read-only aggregation of AI Provider Call records. Optional `from_at` and `to_at` query parameters filter the report window. No new database tables are required.


## v0.2.20 migration

Before using Human Approval endpoints, apply Alembic revision `9f3a1c7b2d10`: `alembic upgrade head`. Existing tenant Admin roles receive `approval.read` and `approval.decide` during the migration.

## v0.2.21 external email Tool

The first side-effecting external Tool is `send_email`. It is available only when explicitly allowed in an EmployeeVersion, requires `run.execute`, always requires Human Approval, and refuses execution unless `SMTP_ALLOWED_RECIPIENT_DOMAINS` is configured. Configure SMTP values in the real `.env`; never commit or package credentials.


## RAG in Employee Runs (v0.2.24)

RAG is now connected to the real Run execution path. It is opt-in per immutable `EmployeeVersion.rules`:

```json
{
  "rag": {
    "enabled": true,
    "top_k": 5,
    "query_fields": ["message"]
  }
}
```

When enabled, RunService builds a query only from the explicitly configured input fields, retrieves tenant-scoped indexed chunks, and passes them through `ExecutionContext.retrieved_context` into Prompt + Context Assembly before the AI Gateway call. Retrieved documents are labeled as untrusted reference material and are not treated as system instructions. Retrieval metadata is recorded in the Audit Log and AI Provider Call metadata.

RAG remains local-development friendly: embeddings use the configured LM Studio embedding model and the current foundation stores vectors in PostgreSQL JSONB.


## Employee Memory (v0.2.25)

Employee memory is durable, tenant-scoped and Employee-scoped. Memory retrieval is opt-in through `EmployeeVersion.rules.memory` with explicit `query_fields`, bounded `top_k`, and `min_score`. Memory is stored with embeddings and is presented to the model as reference context, not provider-level instructions. Real credentials remain in `.env`.


## v0.2.32 Workflow Timeout & Cancellation

- Workflows may opt into a bounded runtime with `max_runtime_seconds`.
- Workflow runs persist `deadline_at` and support cooperative cancellation via `POST /api/v1/workflows/{workflow_id}/runs/{run_id}/cancel`.
- New permission: `workflow.cancel`.
- Celery Beat periodically sweeps overdue workflow runs.
- Cancellation/timeout is cooperative and does not forcibly terminate an already-running external process.
