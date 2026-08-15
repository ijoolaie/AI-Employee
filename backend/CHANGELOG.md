## 1.0.0-rc.8 — 2026-08-12

- Gate 2 runtime certification preparation and release-version consistency fixes.
- Health endpoints now report RC8 consistently with application metadata.
- Corrected the E2E contract test to resolve the repository-level Docker Compose file.


## RC8 TESTFIX3 — 2026-08-12

- Fixed `LMStudioProvider` to resolve settings at construction time instead of module import time.
- This preserves test/runtime overrides of `get_settings()` and prevents a Docker-specific `LM_STUDIO_BASE_URL` from leaking into registry unit tests.
## Phase 9 Ver.11 — Workflow execution fix
## 1.0.0-rc.7 — 2026-08-12

- Added production security headers and production configuration fail-fast validation.
- Added CI production certification workflow for backend, frontend and Docker smoke stack.
- Added k6 smoke workload and environment certification gate.
- Added launch, security, GDPR and performance certification checklist.
- Updated frontend release contract coverage for sales-critical workspaces.

- Fixed workflow execution treating an empty `condition: {}` object as an active condition.
- Empty/default condition objects on normal Employee steps are now treated as "no condition".
- This prevents `ValidationAppError: Unsupported context path: ` during `workflow.execute` for ordinary Employee steps.
- Existing non-empty workflow conditions continue through the deterministic condition evaluator.
- Validation performed: `python -m py_compile backend/app/services/workflow_service.py`.
- Full pytest execution in the packaging environment was blocked because `asyncpg` is not installed there; this is an environment dependency issue, not a test failure.
# v0.9.3 — Autonomous Employee Runtime

- Added opt-in `app.agents.planner` autonomous planning layer.
- Integrated the planner into `RunService` without bypassing the existing Tool Registry execution boundary.
- Added `autonomy` EmployeeVersion rules with bounded plan length and fail-closed planning by default.
- Added autonomous-plan context to Prompt Assembly and audit events for plan creation/failure.
- Existing Memory retrieval/auto-extraction and Tool Registry capabilities are now part of the autonomous runtime path.
- LM Studio remains the default local provider.

## v0.9.1 — Frontend Orders + Sales pages

- Customer pages: `/orders`, `/sales` with summary metrics and status/stage actions.
- API client: listOrders, getOrderSummary, updateOrderStatus, listDeals, getSalesPipeline, getSalesForecast, updateDealStage.
- Types for BusinessOrder, BusinessDeal, pipeline, forecast.
- Sidebar nav entries for Orders and Sales.
- Frontend contract tests extended.

## v0.9.0 — Phase 9: Sales Employee (BusinessDeal)

- Model + migration `c2d3e4f5a6b9` (`business_deals`).
- `sales_service` + tools + REST `/api/v1/sales`.
- Seed: `python scripts/seed_sales_employee.py`.
- Pipeline summary + simple weighted forecast.
- Docs: scope-lock + as-built Phase 9.

## v0.8.0 — Phase 8: Order Employee (BusinessOrder)

- Model + migration `b1c2d3e4f5a8` (`business_orders`).
- `order_service` + tools + REST `/api/v1/orders`.
- Seed: `python scripts/seed_order_employee.py`.
- Tests: `tests/test_order_service.py`.
- Docs: scope-lock + as-built Phase 8.

## v0.7.1 — Invoice tax_rate normalization (post LM Studio E2E)

- `normalize_tax_rate()`: values in (0, 1] treated as fractions (0.09 → 9%), others as percent points.
- Tool + schema descriptions clarified.
- Unit tests for fraction/percent paths.
- Phase 7 E2E with LM Studio recorded as PASS (create_invoice, list, export-pdf, summary).

## v0.7.0 — Phase 7: Invoice Employee (BusinessInvoice)

- Added `BusinessInvoice` model + migration `a0b1c2d3e4f7` (no Stripe naming collision).
- Added `invoice_service` (create, status, analyze file, PDF export via reportlab, financial summary).
- Registered tools: create_invoice, update_invoice_status, analyze_invoice_file, export_invoice_pdf, invoice_financial_summary.
- REST API under `/api/v1/invoices`.
- Seed: `python scripts/seed_invoice_employee.py`.
- Tests: `tests/test_invoice_service.py`.
- Docs: `67_PHASE_7_INVOICE_EMPLOYEE_AS_BUILT_v0.7.0.md`, `23_AS_BUILT_CURRENT_STATE_v0.7.0.md`.

## v0.6.1 — Real-model verification + Phase 7 scope lock (docs only)
- User-reported real LM Studio model run of `test_ai_providers.py` and Document/Report Employee real-stack E2E: PASS. Anthropic provider explicitly not tested (deferred at project owner's direction). See `documents/65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`.
- Phase 7 (Invoice Employee) scope-locked; Roadmap Employee numbering reconciled (Order Employee → Phase 8, Sales Employee → Phase 9). See `documents/66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.
- Fixed stale `0.4.2` version string in `app/main.py` (FastAPI metadata + both health endpoints) to `0.6.1`.
- No functional code change; test suite unchanged at 121 passed in the build environment.

## v0.6.0 — Phase 6: real Stripe payment-provider adapter (closing the Phase 4 commercial gate)
Context: user chose to close the Phase 4 commercial exit gate before continuing the Employee sequence; see `documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`.
- Added `app/services/stripe_service.py` (Checkout Session creation, Billing Portal session creation, webhook signature verification via the Stripe SDK's HMAC-SHA256 scheme, webhook-event-to-billing-state translation).
- Added `POST /api/v1/billing/checkout`, `POST /api/v1/billing/portal`, `POST /api/v1/webhooks/billing/stripe`.
- `billing_service.py` (provider-neutral core) unchanged.
- No new Alembic migration; head unchanged at `0a1b2c3d4e5f`.
- Backend test suite: 121 passed in the build environment (113 carried over + 8 new), including offline HMAC signature verification/rejection tests against a real, independently-constructed signature.
- Real Stripe API calls could not be exercised in this delivery environment (no network egress to Stripe); see the As-Built document's verification boundary and required manual steps.

## 0.4.1 — Outbox hardening + version synchronization

- Clarified the durable Outbox delivery lifecycle: workflow messages are marked `dispatched` when accepted by Celery, while `email.send` remains `processing` until the email worker completes the SMTP side effect.
- Added the missing OpenTelemetry `outbox.status=queued` attribute for email handoff spans.
- Added regression coverage for the Outbox dispatch/telemetry contract.
- Verified the live E2E path with PostgreSQL, Redis, Celery Worker and Beat: workflow Outbox records reached `dispatched` and the resulting Workflow Runs completed successfully.
- Synchronized FastAPI metadata, `/health`, `/health/dependencies`, backend package metadata and frontend package metadata to `0.4.1`.
- Added the Phase 4 baseline audit record and confirmed that the Roadmap Phase 4 Monetization gate remains open.

## 0.2.47 — Developer Console + migration hardening

- Added tenant-scoped audit-log inspection endpoint.
- Added Developer Console operational metrics and dead-letter recovery contracts.
- Added `documents/57_PHASE_1_DEVELOPER_CONSOLE_AS_BUILT_v0.2.47.md`.
- Preserved Phase 1 Prometheus/OpenTelemetry instrumentation and manual worker spans.
- Extracted workflow condition evaluation into a dedicated service module.
- Fixed migration `f8d9e0a1b234` so the existing workflow version uniqueness constraint is not recreated.
- Backend version aligned to 0.2.47 (`pyproject.toml` and `main.py`).

## 0.2.45 — Customer Dashboard

- Added tenant-scoped Customer Dashboard API and complete operational Customer Dashboard UI.
- Added `documents/55_PHASE_1_CUSTOMER_DASHBOARD_AS_BUILT_v0.2.45.md`.
- Updated stale migration-head regression assertion to the current single head.
- Frontend and backend version aligned to 0.2.45.

## 0.2.44 — Platform Admin Dashboard

- Added a distinct `users.is_platform_admin` security boundary; tenant superusers are not platform administrators.
- Added platform-admin protected `/api/v1/admin/dashboard` and `/api/v1/admin/tenants` endpoints.
- Added platform-wide tenant, user, workflow, run, AI call, token, cost and Outbox metrics.
- Added tenant and provider breakdowns with correlated SQL aggregation to avoid cross-join inflation.
- Added PostgreSQL, Redis, Celery worker and AI provider health probes.
- Added Customer Panel link to Platform Admin only for platform-admin users.
- Added `/admin` overview and `/admin/tenants` inventory UI.
- Added explicit `backend/scripts/promote_platform_admin.py` operator bootstrap utility.
- Added `documents/53_ADMIN_DASHBOARD_AS_BUILT_v0.2.44.md`.
- Frontend and backend version aligned to 0.2.44.

## 0.2.43

- Added Schedule UI with tenant-scoped durable workflow schedule catalog.
- Added schedule creation, pause/resume, deletion, next/last run visibility, and cron/timezone management.
- Added tenant-scoped schedule list/update/delete APIs with workflow names.
- Added audit events for schedule updates and deletions.
- Bumped backend/frontend application versions to 0.2.43.

## 0.2.41
- Backend API contract for durable workflow approvals is consumed by the unified customer approval center.
- No database migration required; existing workflow approval decision endpoint remains tenant-scoped, RBAC-protected, audited, and durable.

## 0.2.40 — Workflow Management API

- Added tenant-scoped workflow run listing endpoint.
- Run history is limited to the latest 100 runs and ordered by creation time.
- Existing version activation, replay, cancellation, and observability endpoints are now consumed by the management UI.

## 0.2.38 — Workflow Versioning & Execution Immutability

- Immutable WorkflowVersion execution contracts with deterministic SHA-256 content hashes.
- WorkflowVersion create/list/get/activate APIs.
- Workflow runs can explicitly target a historical WorkflowVersion.
- Run-local execution contract snapshots preserve EmployeeVersion bindings.
- Replay creates a new run against the exact source WorkflowVersion and source execution contract.
- Database-level protection rejects mutation/deletion of WorkflowVersion definitions.
- Added single-current-version invariant and version-number uniqueness.

## 0.2.37 — DLQ, Replay & Observability

- Outbox dead-letter state after configurable maximum attempts.
- Tenant-scoped DLQ inspection and replay API.
- Prometheus metrics endpoint and request metrics.
- Optional OpenTelemetry tracing baseline.

# v0.2.37

- Added transactional-outbox DLQ state and replay API.
- Added tenant-scoped operational metrics and Prometheus endpoint.
- Added optional OpenTelemetry tracing initialization.

## 0.2.36 — Real Stack E2E Infrastructure
- Added reproducible PostgreSQL 16 + Redis 7 + API + Celery Worker + Beat Docker Compose stack.
- Added fail-closed dependency health checking.
- Added E2E verification scripts.
- Added Alembic merge migration for all Phase 1 heads.

## 0.2.35 — Security Hardening

- Added Redis-backed rate limiting and webhook payload limits.
- Added webhook replay protection with signed timestamps.
- Added webhook secret rotation and audit trail.
- Added secret rotation timestamp migration.

## v0.2.32 — Workflow timeout and cancellation

- Added workflow run deadline persistence.
- Added cooperative cancellation endpoint and RBAC.
- Added timeout sweep and terminal timeout state.
- Added audit coverage for timeout/cancellation.

## v0.2.24-LMSTUDIO — RAG runtime context integration

- Connected Knowledge Base retrieval to Employee Run execution.
- Added explicit RAG policy/query-field selection and prompt safety labeling.
- Added retrieval audit/provider metadata.
- Corrected waiting Run completion semantics.

# v0.2.23-LMSTUDIO — RAG / Knowledge Base Foundation

- Added tenant-scoped knowledge document/chunk persistence.
- Added text extraction and deterministic chunking with overlap.
- Added LM Studio embeddings using `text-embedding-nomic-embed-text-v1.5`.
- Added tenant-scoped cosine-similarity retrieval API.
- Added audit coverage for knowledge indexing.
- Added optional PDF/DOCX extraction dependencies.
- Kept embeddings in PostgreSQL JSONB for local-stack compatibility; vector-store replacement remains an explicit future boundary.
- Retrieved knowledge is not yet automatically injected into Run prompts; prompt integration is the next RAG step.

## v0.2.21 — First side-effecting external Tool: approved SMTP email

- Added `send_email` to the controlled Tool Registry.
- `send_email` is side-effecting, requires `run.execute`, and always requires Human Approval.
- Added SMTP configuration and fail-closed recipient-domain allowlisting.
- Added mocked SMTP tests and preserved the existing approval/audit/Celery path.
- No database migration.

## v0.2.18-LMSTUDIO — 2026-08-07 — Controlled Tool Registry and execution boundary

- Added provider-neutral `ToolCall` support to the AI schemas.
- Added a code-registered Tool Registry with explicit JSON Schemas and fail-closed unknown-tool handling.
- Added two deterministic, side-effect-free built-in tools: `calculator` and `current_time`.
- EmployeeVersion `allowed_tools` now resolves through the registry; unknown names fail before the model call.
- Added the controlled model → tool → model loop to Run execution with a configurable maximum iteration count.
- LM Studio and Anthropic provider message serialization/parsing now supports tool calls.
- Tool executions are recorded as `tool.call` Audit Log events and therefore appear in Run Trace without a new database table or migration.
- Added `GET /api/v1/employees/available-tools` for tenant users with `employee.read`; the endpoint exposes schemas only and never directly executes a tool.
- Added an Employee creation UI selector for explicitly allowed tools.
- Added focused registry/provider tests: 6 passed.
- No database migration introduced. Real `.env` remains excluded from release archives.

## v0.2.17-LMSTUDIO — Usage & Cost reporting

- Added `app/services/usage_service.py` for tenant-scoped aggregation of existing AI Provider Call records.
- Added `app/schemas/usage.py`.
- Added `GET /api/v1/usage/summary`, protected by the existing `audit.read` permission.
- Added optional `from_at` / `to_at` filters.
- No database migration required.
- Added focused Usage response-contract coverage.

## v0.2.14-LMSTUDIO — 2026-08-07 — Hardened JSON Schema Validation

- Promoted the validation layer to the `v0.2.14` implementation baseline.
- Enabled JSON Schema `format` assertions through `jsonschema.FormatChecker`.
- Added bounded multi-error reporting (maximum 5 errors) while retaining deterministic primary error fields for API compatibility.
- Added schema-path information to validation errors for faster diagnosis.
- Added support tests for nested constraints, enums, local `$ref` JSON Pointer references and email format validation.
- Rejected external `$ref` and `$dynamicRef` resources so tenant/Employee-controlled schemas cannot trigger unintended network or filesystem resolution during validation.
- Kept provider independence: validation occurs at the Employee/Run contract boundary, not inside LM Studio or Anthropic providers.
- Updated package version and As-Built documentation.

## v0.2.13-LMSTUDIO — 2026-08-07 — Prompt + Context Assembly

- Added `backend/app/ai/prompt_assembly.py` as the deterministic, provider-agnostic boundary for Employee prompt/context assembly.
- Added `ExecutionContext` extension points for rules, tenant context, retrieved context and memory without coupling them to a provider.
- Moved Employee prompt rendering out of `run_service.py`; RunService now supplies validated EmployeeVersion data and execution context to the assembler.
- Prompt templates now fail with a structured `ValidationAppError` when they reference missing input fields instead of producing an unhandled `KeyError`.
- User input is serialized as stable UTF-8 JSON rather than Python `str(dict)` before being sent to the model.
- Employee rules are included as an explicit system-context section; RAG, memory and tenant context remain empty extension points until their respective modules land.
- `allowed_tools` is tracked in assembly metadata, but no provider tool definitions are fabricated before a Tool Registry exists.
- AI Provider Call `raw_meta` and Audit metadata now preserve non-sensitive prompt-assembly metadata (`assembly_version`, message/tool counts and populated context sections).
- Added focused prompt-assembly tests.
- Backend package version bumped to 0.2.13.
- Updated As-Built, setup, manifest and package changelog documentation.

## v0.2.12-LMSTUDIO — 2026-08-07 — JSON Schema validation

- Replaced Run input validation's required-key placeholder with Draft 2020-12 JSON Schema validation.
- Added output validation against the current EmployeeVersion output schema before a Run can become `success`.
- Added schema-definition validation when creating Employees and publishing Employee versions.
- Added `app/services/schema_validation.py` with structured validation errors compatible with `ValidationAppError`.
- Preserved provider token/cost accounting when output validation fails, while recording the Run as failed and committing the existing Audit Log path.
- Added `tests/test_schema_validation.py` covering valid/invalid input, output contracts, empty schemas and invalid schema definitions.
- Updated As-Built/Current-State documentation and package manifest.

## v0.2.11-LMSTUDIO — 2026-08-07 — AI Gateway observability correction

- Fixed AI Gateway latency recording: `Timer.duration_ms` is finalized only after the context exits, so the Gateway now reads the live elapsed duration inside `finally`.
- Added Gateway-enriched `ChatResult.latency_ms` and `ChatResult.cost_usd` so cost/latency are calculated once at the Gateway boundary.
- Updated Run execution to consume Gateway-calculated cost instead of recalculating provider cost.
- Added automated coverage for live latency and single-source cost tracking.
- Verified against the v0.2.10-LMSTUDIO baseline, including the successful LM Studio/Gemma/Celery end-to-end path.

## v0.2.10-LMSTUDIO — 2026-08-07 — Windows Celery asyncpg lifecycle fix

- Fixed the Windows Celery/asyncpg failure observed after a real Run reached the worker: `AttributeError: 'NoneType' object has no attribute 'send'` from `asyncio.proactor_events`.
- Added `worker_db_session()` in `backend/app/core/database.py`. Each Celery task now gets a worker-local async engine using SQLAlchemy `NullPool`, preventing asyncpg connections from being reused across the event loops created by `asyncio.run()`.
- Kept the API request engine pooled; the isolation is specific to Celery worker execution.
- Preserved the existing Windows Celery requirement: `--pool=solo`.
- Updated the As-Built/Current-State documentation to distinguish the observed failure, implemented fix, and pending E2E verification.

# Changelog

## [0.2.7] — 2026-08-07

- Fixed PostgreSQL RBAC registration failure caused by using SQLAlchemy generic `insert()` with PostgreSQL-only `on_conflict_do_nothing()`.
- Switched `auth_service.py` to `sqlalchemy.dialects.postgresql.insert`.
- Kept registration transaction atomic so failed permission/role provisioning rolls back tenant and user creation.
- Bumped the FastAPI/OpenAPI backend version from 0.2.6 to 0.2.7.

## [0.2.6] — 2026-08-07

- Corrected FastAPI application version exposed by `/api/v1/openapi.json` and Swagger UI from stale `0.2.3` to `0.2.6`.
- Preserved the async-safe RBAC registration fix from 0.2.5.

## [0.2.4] - Phase 1 Core — RBAC enforcement

- Added endpoint-level RBAC permission checking.
- Added tenant-scoped Admin role provisioning for the first registered user.
- Added Core permission catalog for Employee, Run, File and Audit operations.
- Loaded user roles/permissions into the authenticated Tenant Context.
- Protected Employee, Run and File endpoints with least-privilege permissions.
- Added unit tests covering permission grants and cross-tenant role isolation.

# AI Employee Platform — Backend Changelog

## v0.2.0 — 2026-08-06

Implements the Phase 1 remainder + Phase 2 groundwork agreed in docs v1.2
(`21_CrossCutting_Additions_v1.0`). Build order followed: B (finish
Identity) → C (Files) → D (AI Gateway skeleton) → E (Employee/Run skeleton).

### Added
- `app/models/audit_log.py`, `app/services/audit_service.py` — Audit Log,
  independent Core module. Wired into: auth login/register, employee
  create/version-publish, run create/complete, ai provider call, file
  upload/delete.
- `app/core/logging.py`, `app/core/middleware.py` — structured JSON
  logging, request-scoped context vars, `X-Request-ID` correlation.
- `app/models/file.py`, `app/services/storage.py`, `app/services/file_service.py`,
  `app/api/v1/files.py` — File upload/list/soft-delete, local-disk storage
  backend (S3-compatible backend is a drop-in swap later).
- `app/ai/` — AI Gateway: `schemas.py` (provider-agnostic request/result
  types), `providers/base.py` (Provider interface), `providers/anthropic_provider.py`
  (the one connected provider for v1), `gateway.py` (routes calls, records
  latency/tokens/cost to `ai_provider_calls`, writes to Audit Log).
- `app/models/employee.py` (`Employee`, `EmployeeVersion`) — versioned
  Employee definitions; `app/services/employee_service.py`;
  `app/api/v1/employees.py`.
- `app/models/run.py` (`Run`), `app/models/ai_provider_call.py`
  (`AIProviderCall`) — `app/services/run_service.py` implements the
  execution model from `11_Employee_Framework` §5 (validate input →
  execute via AI Gateway → store output/cost); `app/api/v1/runs.py`.
- `app/workers/celery_app.py`, `app/workers/run_worker.py` — async Run
  execution via Celery.
- Initial Alembic migration (`alembic/versions/*_initial_core_schema.py`) —
  generated via `alembic revision --autogenerate` against all models above
  plus the existing Identity models, and applied/verified against a real
  PostgreSQL 16 instance (13 tables).
- `app/core/config.py` — added `storage_dir`, `ai_default_provider`,
  `anthropic_api_key`, `ai_default_model` settings.

### Changed
- `app/main.py` — registers `RequestContextMiddleware`, calls
  `configure_logging()` on startup.
- `app/core/deps.py` — binds tenant/user into the logging context once
  auth resolves the caller (`get_tenant_context`).
- `app/services/auth_service.py` — records `auth.login` (success/failure)
  and `tenant.registered` audit entries.
- `app/api/v1/router.py`, `app/models/__init__.py`, `alembic/env.py` —
  wired in all new routers/models.

### Fixed
- `app/workers/run_worker.py` — the failure path was calling
  `db.rollback()` after `run_service.execute_run()` had already flushed
  the failure state (Run.status=failed, error, audit entries, the
  `ai_provider_calls` row) onto the same session, silently discarding all
  of it. Failure paths now `db.commit()` that state instead — verified via
  smoke test that a failed Run's `error`, `audit_logs`, and
  `ai_provider_calls` rows all persist correctly.

### Verified
- `alembic upgrade head` against real PostgreSQL 16 — clean, 13 tables.
- End-to-end smoke test (register → login → create Employee → create Run
  → Celery executes → AI Gateway attempt fails without an API key →
  failure correctly recorded on `Run`, `audit_logs`, `ai_provider_calls`).
- `pytest` — existing unit tests pass.

### Not yet done (tracked for next revision)
- JSON Schema validation of Run input/output (currently only checks
  `required` keys are present — see `run_service._validate_input`).
- Output Schema enforcement, Human Approval gate (`11_Employee_Framework` §5 steps 7–8).
- Integration tests for the new modules (only the pre-existing security
  unit tests are in `tests/` — Employee/Run/File/Audit paths were verified
  manually via the smoke test above, not yet automated).
- RBAC/permission checks on the new endpoints (currently any authenticated
  user in a tenant can create Employees/Runs/Files — Role/Permission
  models exist but aren't enforced on these routes yet).

---

## v0.1.0 — initial scaffold
Identity layer: Tenant, User, Role/Permission, JWT auth (register/login/refresh/me).

## [0.2.3] — 2026-08-06

### Changed
- Auth service uses `AppError` (`UnauthorizedError` / `ConflictError`) instead of raw `HTTPException`.
- Global `HTTPException` handler returns the standard `{success, error:{code,message}}` envelope (deps/JWT paths too).
- `RunResponse` includes optional `employee_name` and `employee_slug` for UI lists.

## [0.2.2] — 2026-08-06

### Docs / DX
- `psycopg2-binary` added to requirements (Alembic sync migrations on Windows/Linux).
- README: Windows Celery `--pool=solo`, alembic revision mismatch reset, PowerShell notes.

## [0.2.1] — 2026-08-06

### Fixed / improved for Frontend integration
- `GET /api/v1/runs` now accepts optional query param `employee_id` so the
  Customer Panel employee-detail page can list runs for one employee only.

## Trace surface — cumulative update

- Added `app/services/trace_service.py`.
- Added `app/schemas/trace.py`.
- Added tenant-scoped `GET /api/v1/runs/{run_id}/trace` under `run.read` authorization.
- Trace is derived from existing Run, AIProviderCall and AuditLog records; no schema migration is required.
- Backend source compilation: PASS.

## v0.2.25 — Employee Memory Foundation

Durable tenant-scoped Employee memory is now available and can be explicitly enabled in EmployeeVersion rules. Memory retrieval is integrated into the Run context path and uses the existing LM Studio embedding service.

## v0.2.26
- Automatic Employee Memory Extraction & Consolidation added.
- Opt-in rules: `memory.auto_extract`, `max_candidates`, `min_importance`, `dedup_threshold`.
- Extraction uses `AIGateway` and is recorded as a normal provider call.
- Candidate secrets are rejected and duplicate memories are consolidated conservatively.
- Extraction failures are best-effort and do not fail the parent Run.

## 0.2.31
- Durable Workflow Human Approval with wait/resume, expiration, RBAC and audit.

## v0.2.33 — Workflow Execution Hardening
- Parallel workflow branches with durable fan-out/join.
- Persisted retry/recovery state with bounded exponential backoff.
- Workflow Run and Step Run idempotency safeguards.
- Durable Outbox deduplication keys.
- Workflow execution row locking.
- Workflow Observability API.
- Full pytest/PostgreSQL migration remain NOT VERIFIED in the delivery environment.

## 0.2.39
- Added Phase 1 Visual Workflow Builder foundation in the customer frontend.
- Builder creates immutable workflow versions through the existing version API.
- Added workflow builder navigation and As-Built documentation.


## v0.2.47
- Completed Phase 1 OpenTelemetry and Prometheus instrumentation.
- Added FastAPI/SQLAlchemy auto-instrumentation and reusable manual worker/AI spans.
- Added AI token/cost/latency metrics, workflow metrics, Celery metrics, Outbox/DLQ gauges and dependency health metrics.
- Added observability contract tests.

## v0.3.0 — Phase 2: Report Employee
- Added `analyze_dataset` Tool + `app/services/report_service.py` (pandas/matplotlib/reportlab/openpyxl).
- Added System Employee `report-employee` via `scripts/seed_report_employee.py`.
- Added `GET /api/v1/files/{file_id}/download` (closes a Phase 1 gap).
- Added whitelisted `report_artifacts` carry-through onto `Run.output_data`.
- No new Alembic migration; Alembic head unchanged at `7a2b3c4d5e6f`.
- Backend test suite: 91 passed in the build environment; see `documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md` for the full verification boundary.

## v0.4.0 — Phase 3: Validation tooling (+ Phase 2 closed)
- Phase 2 CLOSED per user-reported real-environment test (2026-08-09).
- Added `feedback` table (migration `b3c4d5e6f713`, down_revision `7a2b3c4d5e6f`) + `POST`/`GET /api/v1/feedback`.
- Added `GET /api/v1/admin/validation` (Phase 3 exit-criteria tracking: active-tenant count vs target of 3, feedback aggregates).
- Added `feedback.create`/`feedback.read` permissions, seeded onto the tenant Admin role.
- Backend test suite: 97 passed in the build environment; `test_v036_e2e_contract.py` updated for the new Alembic head `b3c4d5e6f713`.
- See `documents/59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md` for the full scope note and verification boundary.

## 0.4.2 — Monetization

- Added billing plan/subscription/billing-event models and migration.
- Added provider-neutral billing service and API.
- Added quota enforcement at run/employee/workflow service boundaries.
- Added platform billing/MRR summary and Phase 4 regression contracts.

## v0.5.0 — Phase 5: Document Employee (started ahead of Phase 4 commercial exit gate)
Governance note: per `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, this Phase was gated behind Phase 4's commercial exit criterion, which remains "not yet proven" per `62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md`. Started at explicit user direction; see `documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`.
- Added `analyze_document` Tool + `app/services/document_service.py` (pypdf/pdf2image/pytesseract/python-docx-based extraction, OCR eng+fas, regex field detection, keyword document-type classification).
- Added System Employee `document-employee` via `scripts/seed_document_employee.py`.
- Extended `report_artifacts`/`document_artifacts` whitelisted carry-through onto `Run.output_data`.
- No new Alembic migration; Alembic head unchanged at `0a1b2c3d4e5f`.
- Backend test suite: 113 passed in the build environment (103 carried over + 10 new); fixed a pre-existing `test_v036_e2e_contract.py` gap (still asserted the Phase 3 head) found in the uploaded v0.4.2 package.
- New system dependencies required: `tesseract-ocr`, `tesseract-ocr-fas`, `poppler-utils` (see DEV_SETUP.md).

## 1.0.0-rc.6 — 2026-08-12
- Added tenant-scoped ROI analytics endpoint.
- Added Employee Template catalog and installation flow.
- Added immutable Employee guardrails read/update endpoints.
- Added customer privacy export and anonymization endpoints with audit log.
- Updated frontend navigation, Analytics, Onboarding, Employee detail, Templates, and Privacy pages.
