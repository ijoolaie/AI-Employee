## 2026-08-12 — RC8 Docker Compose interpolation hardening

- Escaped Docker Compose shell variables in the frontend healthcheck (`$$HOSTNAME`, `$$HOST_IP`) so Compose no longer attempts to substitute them from the host environment.
- Eliminates the `HOSTNAME` / `HOST_IP` unset warnings seen during `docker compose up` / `down`.
- Preserves the existing container-IP healthcheck behavior that was verified as healthy on the Windows Docker environment.


## 2026-08-11 — Product Workspace Architecture

- Reorganized tenant navigation into Business, AI Workspace, Operations, and Developer areas.
- Added `/workspace` as the dedicated AI Workspace entry point.
- Clarified Platform Admin as a separate control-plane surface.
- Documented the four product surfaces: Platform Admin, Business Dashboard, AI Workspace, and Customer Experience.

## 2026-08-11 — Client handoff / verification documentation

- Added `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` with the complete current test/evidence matrix.
- Corrected current documentation to identify `0a1b2c3d4e5f` as the final Alembic head for the supplied migration graph.
- Recorded real Redis/Celery worker verification and successful `run.execute` completion (13.61s).
- Recorded the observed Windows Celery `prefork` / `WinError 5` issue and the `--pool=solo` development recommendation.
- Recorded the exact limitations of the fresh backend pytest review (`asyncpg` missing in the review environment).
- Updated current master guide, Windows runbook, release audit, test execution plan and as-built current-state documentation.
- No application runtime code was changed by this documentation update.

## Phase 9 Ver.11 — Workflow execution fix

- Fixed workflow execution treating an empty `condition: {}` object as an active condition.
- Empty/default condition objects on normal Employee steps are now treated as "no condition".
- This prevents `ValidationAppError: Unsupported context path: ` during `workflow.execute` for ordinary Employee steps.
- Existing non-empty workflow conditions continue through the deterministic condition evaluator.
- Validation performed: `python -m py_compile backend/app/services/workflow_service.py`.
- Full pytest execution in the packaging environment was blocked because `asyncpg` is not installed there; this is an environment dependency issue, not a test failure.
## v0.9.2 — CORS fix for frontend (localhost:3000)

- CORSMiddleware is now the **outermost** middleware so rate-limit and early responses still include Access-Control-Allow-Origin.
- `cors_origins` accepts comma-separated env values; defaults include localhost and 127.0.0.1:3000.
- docker-compose sets `CORS_ORIGINS` for the api service.

## v0.9.1.1 — Fix EmptyState icon on Orders/Sales pages

- Pass required `icon` prop to EmptyState (ShoppingCart / TrendingUp).

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

- Verification: backend 77 unit tests passed; frontend contract 28 passed.
- `test_tool_registry` updated to include Phase 7 invoice tools.

- Added `BusinessInvoice` model + migration `a0b1c2d3e4f7` (no Stripe naming collision).
- Added `invoice_service` (create, status, analyze file, PDF export via reportlab, financial summary).
- Registered tools: create_invoice, update_invoice_status, analyze_invoice_file, export_invoice_pdf, invoice_financial_summary.
- REST API under `/api/v1/invoices`.
- Seed: `python scripts/seed_invoice_employee.py`.
- Tests: `tests/test_invoice_service.py`.
- Docs: `67_PHASE_7_INVOICE_EMPLOYEE_AS_BUILT_v0.7.0.md`, `23_AS_BUILT_CURRENT_STATE_v0.7.0.md`.

## v0.6.1 — Real-model verification + Phase 7 scope lock (documentation release, no functional code change)

- Recorded a **user-reported** real-model (LM Studio) verification pass:
  `test_ai_providers.py` and the Document/Report Employee real-stack E2E
  flows were run against a real LM Studio model outside this delivery
  environment and reported as passing. The Anthropic provider was
  explicitly **not** tested, at the project owner's direction. See
  `documents/65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`.
- Scope-locked **Phase 7 (Invoice Employee)** and resolved the Phase 6
  numbering collision between the Roadmap's "فاز ششم" and this project's
  Stripe-adapter release. Order Employee and Sales Employee are now
  Phase 8 and Phase 9. No Phase 7 code exists yet. See
  `documents/66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.
- Fixed a stale `0.4.2` version string in `backend/app/main.py` (FastAPI
  `version=` kwarg and both health-check endpoints) to `0.6.1`, matching
  `backend/pyproject.toml` and `frontend/package.json`.
- No new automated tests in this release (documentation/version-string
  only); backend suite remains 121 passed in the build environment.
- Full detail: `RELEASE_VERIFICATION_v0.6.1.md`.

## v0.6.0 — Phase 6: real Stripe payment-provider adapter (closing the Phase 4 commercial gate)

**Context**: after Phase 5 (Document Employee) was built ahead of the
Phase 4 commercial exit gate at explicit user direction, the user was
asked whether to continue the Employee sequence (a further "Phase 6") or
return and close that gate first. **The user chose to close the gate.**
This release is that work. See
`documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`.

- Added `app/services/stripe_service.py`: real Stripe Checkout Session
  creation (paid-plan subscription), real Stripe Billing Portal session
  creation (self-serve upgrade/downgrade/cancel), and Stripe webhook
  signature verification + event-to-billing-state translation.
- Added `POST /api/v1/billing/checkout`, `POST /api/v1/billing/portal`,
  and the public `POST /api/v1/webhooks/billing/stripe` receiver (mounted
  under the existing `/api/v1/webhooks/` prefix, inheriting its payload
  size limit and rate limiting automatically).
- Webhook signature verification was tested with a **real,
  independently-constructed HMAC-SHA256 signature** (not a mock) — signed
  offline per Stripe's documented scheme, confirmed to be both accepted
  when valid and rejected when tampered/wrong-secret/missing.
- `app/services/billing_service.py` (the provider-neutral Phase 4 core:
  quota enforcement, MRR reporting) is **unchanged** — Stripe only feeds
  it via the same `record_event()`/`Subscription` update path any
  provider would.
- Updated the customer Billing page: paid plans now redirect to real
  Stripe Checkout; added a "Manage billing" button linking to the Stripe
  Billing Portal.
- Zero new Alembic migrations — `Subscription.provider`/
  `provider_customer_id`/`provider_subscription_id` already existed from
  Phase 4. Plan→Stripe-Price mapping uses a settings dict, not a new
  table.
- Backend test suite: 121 passed in the build environment (113 carried
  over + 8 new in `tests/test_stripe_service.py`).
- **Important**: real Stripe API calls (Checkout, Portal, a real webhook
  delivery) could not be made from this delivery environment — its
  network egress allowlist does not include Stripe. The Phase 4
  *commercial* exit gate (proven MRR + paid subscribers) is therefore
  still not proven by this release alone; see the As-Built document's
  "Required manual steps" section for what the project owner must do
  next, in an environment that can reach Stripe.

## Release truth
v0.6.0 is the current package baseline: Phase 4's implementation gap is
closed (a real payment adapter now exists and is unit-tested), but its
commercial gate remains open pending a live run. All prior release-truth
statements remain valid for their respective phases.

## 0.4.1 — Outbox hardening + release-version synchronization

- Clarified the durable Outbox lifecycle for workflow/Celery handoff versus email side-effect completion.
- Added `outbox.status=queued` telemetry for the email handoff path.
- Synchronized backend package metadata, FastAPI metadata, health endpoints and frontend package metadata to `0.4.1`.
- Added `documents/60_RELEASE_0.4.1_OUTBOX_HARDENING_AS_BUILT.md`.
- Verified the real Docker workflow path: Outbox → Celery → Workflow Run success (user-reported, 2026-08-09).
- Explicitly preserved the roadmap gate: Phase 4 (Monetization) is not complete; Phase 5 remains blocked by that gate.
- Added `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md` to freeze and document the Phase 4 baseline/audit decision.

## 0.2.47 — Developer Console + migration hardening

- Added tenant-scoped Phase 1 Developer Console at `/developer`.
- Added tenant-scoped audit-log inspection API and frontend view.
- Added operational metrics, recent runs, DLQ inspection and replay controls to the Developer Console.
- Added `documents/57_PHASE_1_DEVELOPER_CONSOLE_AS_BUILT_v0.2.47.md`.
- Preserved the Phase 1 OpenTelemetry and Prometheus observability implementation from v0.2.46 (`documents/56_OPENTELEMETRY_METRICS_AS_BUILT_v0.2.46.md`).
- Extracted workflow condition evaluation into `workflow_conditions.py` without removing existing workflow/outbox tracing.
- Fixed Alembic migration `f8d9e0a1b234`: it no longer attempts to recreate `uq_workflow_version_number`, which is already created by the workflow foundation migration.
- Kept frontend and backend release version aligned at 0.2.47 (`pyproject.toml`, `main.py`, `package.json`).

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

## v0.2.41 — Unified Approval UI
- Added workflow approval API bindings to the customer frontend.
- Unified Tool Approval and durable Workflow Approval into one approval center.
- Added workflow approval metadata, expiry visibility, decision reasons, and explicit Resume/Reject actions.
- Added targeted query invalidation for workflow runs after approval decisions.
- Updated frontend/backend package versions to 0.2.41.
- Added As-Built documentation for the approval UI.

## v0.2.40 — Workflow Management UI

- Added tenant-scoped workflow run history endpoint.
- Added Workflow Management detail view with version history and activation controls.
- Added workflow run selection, live status refresh, cancellation, replay, and observability view.
- Added explicit Workflow Version display so each run is visibly tied to its immutable execution version.
- Added missing frontend Tool Approval API bindings used by the existing Approvals page.
- Kept the Visual Builder and immutable Workflow Version model as the source of truth for new versions.

## 0.2.37 — DLQ, Replay & Observability

- Outbox dead-letter state after configurable maximum attempts.
- Tenant-scoped DLQ inspection and replay API.
- Prometheus metrics endpoint and request metrics.
- Optional OpenTelemetry tracing baseline.

## v0.2.36 — Real Stack E2E Infrastructure
- Added reproducible PostgreSQL 16 + Redis 7 + API + Celery Worker + Beat Docker Compose stack.
- Added backend Dockerfile for the E2E stack.
- Added fail-closed `/health/dependencies` readiness endpoint.
- Added real-stack verification scripts; unavailable infrastructure is reported as NOT VERIFIED rather than simulated as PASS.
- Added a merge migration to collapse the historical Phase 1 Alembic heads into one head.
- Added v0.2.36 E2E contract tests and As-Built documentation.

## v0.2.32 — Workflow timeout and cooperative cancellation

- Added optional workflow-level runtime deadline.
- Added `workflow.cancel` RBAC permission and cancellation API.
- Added durable cancellation/timeout state to workflow runs.
- Added Celery Beat timeout sweep and worker-side cooperative cancellation checks.
- Added timeout/cancellation audit events.

## v0.2.24-LMSTUDIO — 2026-08-07 — RAG runtime context integration

- Connected v0.2.23 Knowledge Base retrieval to the actual Employee Run execution path.
- Added opt-in EmployeeVersion RAG policy with explicit `query_fields` and bounded `top_k`.
- Retrieved knowledge now flows through `ExecutionContext.retrieved_context` into Prompt + Context Assembly before the AI Gateway call.
- Retrieval is tenant-scoped, limited to indexed documents and active source files.
- Retrieved content is explicitly marked as untrusted reference material to reduce prompt-injection risk.
- Added retrieval audit event and AI Provider Call RAG metadata.
- Corrected Human Approval waiting semantics so paused Runs are not marked completed.
- Source compilation PASS; full runtime pytest remains environment-dependent when `asyncpg` is absent.

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

- Added `send_email` as the first real side-effecting external integration.
- Tool execution remains behind the existing Registry, EmployeeVersion allowlist, worker-side RBAC and durable Human Approval boundary.
- Added strict JSON Schema validation for recipients, subject and body.
- Added SMTP configuration with a fail-closed recipient-domain allowlist. Empty `SMTP_ALLOWED_RECIPIENT_DOMAINS` denies execution.
- Real SMTP credentials remain environment-only and are never packaged.
- Added focused mocked-SMTP tests; no database migration required.
- Bumped backend package/OpenAPI version to 0.2.21.

## v0.2.20 — Human Approval / Tool Execution Policy

- Added durable `tool_approval_requests` persistence and Alembic migration `9f3a1c7b2d10`.
- Added `waiting` Run state and worker pause/resume semantics for approval-gated Tool calls.
- Added tenant-scoped `approval.read` and `approval.decide` permissions and migrated existing Admin roles.
- Added row-locked approve/reject decision path with audit events and Celery resume.
- Stored validated Tool arguments and serialized continuation messages at the approval boundary.
- Added `/api/v1/approvals` API and Customer Panel `/approvals` page.
- Current built-in Tools remain side-effect-free; no external Tool was enabled by this release.
- Verification: source compilation and focused approval-policy tests PASS.

## v0.2.19 — Tool Security Hardening

- Added explicit per-tool required permission and approval policy metadata.
- Re-authorize tool execution inside the Celery worker using the Run creator's tenant-scoped RBAC permissions.
- Fail closed on missing tool permission.
- Block approval-required tools until Human Approval exists.
- Expose policy metadata through available-tools API.

## v0.2.18-LMSTUDIO — 2026-08-07 — Controlled Tool Registry and execution boundary

- Added a provider-neutral ToolCall contract and controlled Tool Registry.
- Added deterministic `calculator` and `current_time` tools; no external side effects are enabled in this release.
- Connected EmployeeVersion `allowed_tools` to registered tool schemas.
- Added bounded model/tool execution loop through the existing AI Gateway.
- Added tool-call audit events so Run Trace includes tool spans without a new table.
- Added available-tools API and Employee creation UI selection.
- Verification: source compilation PASS; focused tool tests 6 PASS.
- No migration; real `.env` excluded.

## v0.2.17-LMSTUDIO — 2026-08-07 — Usage & Cost reporting

- Added tenant-scoped read-only usage/cost aggregation over existing `ai_provider_calls`.
- Added `GET /api/v1/usage/summary` with optional time-window filters.
- Added provider/model breakdown with calls, success/failure, tokens, cost and average latency.
- Added Customer Panel `/usage` page and navigation entry.
- No database migration introduced; existing AI Provider Call records remain the reporting source of truth.
- Kept billing, quotas, invoicing and provider reconciliation as separate future phases.
- Updated As-Built, current-state, setup/manifest and changelog documentation.

## v0.2.15-LMSTUDIO — 2026-08-07 — Cumulative runtime verification

- Preserved all implemented changes through the hardened JSON Schema Validation baseline.
- Documented the real Windows end-to-end path: authenticated Run creation (201) → Celery → worker-local NullPool DB session → Prompt/Context Assembly → AI Gateway → LM Studio/Gemma → AI Provider Call + Audit Log → Run success → commit.
- Recorded LM Studio smoke test PASS and successful `google/gemma-4-e4b` completion.
- Confirmed local LM Studio cost accounting remains `0.0 USD`.
- Synchronized As-Built, setup, manifest and release-verification documentation.
- Real `.env` remains excluded from the release archive.

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

## v0.2.9-LMSTUDIO — 2026-08-07 — Documentation and verification hardening

- Bumped backend package version to 0.2.9.
- Added provider abstraction tests and LM Studio smoke-test utility.
- Synchronized current-state documentation across the package.
- Kept `.env` out of release archives.
- Windows Celery development mode is documented as `--pool=solo`.

## v0.2.8-LMSTUDIO — 2026-08-07 — Local LM Studio provider

- Added `LMStudioProvider` using LM Studio's OpenAI-compatible `/v1/chat/completions` endpoint.
- Added provider registry/factory so `AIGateway` no longer imports a concrete provider directly.
- Default development provider is `lm_studio`; default model is `google/gemma-4-e4b`.
- Added `LM_STUDIO_BASE_URL` and optional `LM_STUDIO_API_KEY` settings.
- Local inference cost is recorded as `0.0 USD`; latency and model-reported token usage remain observable.
- Anthropic remains available as an optional cloud provider.
- Release packages intentionally exclude the real `.env`; only `.env.example` is shipped.
- Added an explicit Planned / As-Built / Verified baseline document and synchronized documentation appendices.

## v0.2.7 — 2026-08-07 — RBAC registration fix

- Fixed `POST /api/v1/auth/register` HTTP 500 caused by `Insert.on_conflict_do_nothing` not existing on SQLAlchemy generic inserts.
- PostgreSQL-specific `insert` is now imported from `sqlalchemy.dialects.postgresql`.
- Registration now correctly creates the tenant Admin role, Core permissions, role-permission links, and user-role link without the previous AttributeError.
- FastAPI/OpenAPI version is now 0.2.7.

# Ai Core — Phase 1 Step 01

## Scope
RBAC enforcement and tenant-isolation authorization baseline.

## Implemented
- Tenant-scoped Admin role provisioning for the first registered user.
- Core permission catalog:
  - employee.read
  - employee.write
  - run.read
  - run.execute
  - file.read
  - file.write
  - audit.read
- Endpoint-level permission dependencies.
- User role/permission loading in the authenticated Tenant Context.
- Cross-tenant role protection.
- RBAC unit tests.
- Backend version bumped to 0.2.4.

## Verification
- Python source compilation: PASS.
- Full pytest execution: BLOCKED in the delivery environment because the
  uploaded project dependencies are not installed (`python-jose` missing).
  Existing and new tests remain included in the package and should be run
  after installing `backend/requirements.txt` (Python >= 3.11).
## Fix — Async RBAC registration (Step 01 verification)

### Problem found
- Registration returned HTTP 500 after tenant/user creation when `_assign_tenant_admin_role()` accessed `role.permissions` through an async ORM relationship. SQLAlchemy raised `MissingGreenlet` because the access attempted implicit IO outside the async greenlet context.

### Fixed
- RBAC association rows are now written explicitly through `role_permissions` and `user_roles` with PostgreSQL `ON CONFLICT DO NOTHING`.
- Registration no longer reads `role.permissions` or `user.roles` during the transaction.
- Audit role assignment uses the resolved `role.id` directly.
- Registration email normalization is applied consistently to duplicate checks and stored user email.
- This fix does not change the documented RBAC contract or tenant-isolation rules.

### Verification
- Python source compilation: PASS.
- Local pytest execution: BLOCKED in the delivery environment because `python-jose` is not installed.
- Manual reproduction from the user's Windows PostgreSQL environment identified the failure at `auth_service.py:_assign_tenant_admin_role()` and the fix targets that exact failure.


## Current cumulative update — Trace surface

- Added tenant-scoped Run Trace aggregation from existing Run, AI Provider Call and Audit Log records.
- Added `GET /api/v1/runs/{run_id}/trace`.
- Added frontend Run Trace timeline with active-run refresh.
- Corrected frontend terminal success status from `succeeded` to backend-compatible `success`.
- Backend source compilation verified.
- No database migration required for this change.

## v0.2.25 — Employee Memory Foundation

- Added durable `employee_memories` storage.
- Added tenant/Employee-scoped semantic memory retrieval using the existing LM Studio embedding endpoint.
- Added opt-in `rules.memory` execution policy with explicit `query_fields`, bounded `top_k`, and `min_score`.
- Connected memory retrieval to Employee Run Prompt + Context Assembly.
- Added memory CRUD/search API and RBAC permissions.
- Added audit events for memory creation, retrieval, and deletion.
- Automatic memory extraction is deliberately deferred until a safe consolidation/policy layer exists.

## v0.2.26 — Automatic Employee Memory Extraction & Consolidation
- Added explicit opt-in `memory.auto_extract` policy.
- Added bounded candidate extraction via the AI Gateway.
- Added candidate validation and secret-pattern filtering.
- Added semantic deduplication by Tenant + Employee + memory type.
- Added conservative consolidation of higher-quality memory representations.
- Added best-effort failure isolation so memory extraction cannot fail a successful Run.
- Added `memory.auto_extracted` and `memory.auto_extract_failed` audit events.
- Added focused tests and As-Built documentation.


## v0.2.27 — Memory Conflict & Lifecycle

- Added Employee Memory versioning with `version` and `supersedes_id`.
- Added lifecycle states: `active`, `superseded`, `expired`, `deleted`, and `conflict`.
- Added `effective_at` and lifecycle-aware expiry handling.
- Added explicit `conflict_key` and `supersede_memory_id` controls to memory creation.
- Automatic extraction now supports an optional stable `subject_key` for conflict detection and versioned supersession.
- Retrieval now excludes expired/superseded/deleted memories and marks due expirations as `expired`.
- Added audit events for memory supersession and expiration.
- Performed a code-versus-documentation As-Built audit; see `documents/34_AS_BUILT_AUDIT_v0.2.27.md`.
- Corrected stale v0.2.26 baseline/current-state titles in the authoritative current documentation path.
- Full pytest collection remains environment-blocked when `asyncpg` and `python-jose` are absent; no false PASS is recorded.

## v0.2.28 — Workflow Engine Foundation
- Added tenant-scoped versioned Workflow definitions.
- Added manual Workflow Run API and Celery worker.
- Added durable WorkflowRun and WorkflowStepRun state.
- Added linear Employee Action execution with context mapping.
- Added bounded step retry support.
- Added workflow RBAC permissions.
- Added Workflow As-Built and Planned-vs-As-Built audit documents.
- Full pytest is not claimed when runtime dependencies are unavailable.

## Release truth
v0.2.28 is the current package baseline. Historical As-Built snapshots remain intentionally preserved.

## v0.2.33 — Workflow Execution Hardening
- Added durable parallel workflow branches with Celery fan-out and parent join semantics.
- Added persisted retry state and bounded exponential backoff for workflow Employee steps.
- Added crash recovery that reuses a successfully completed Employee Run instead of executing it twice.
- Added Workflow Run `Idempotency-Key` support and database uniqueness.
- Added Workflow Step Run uniqueness and durable Outbox `dedupe_key` support.
- Added Workflow Run row locking during execution to prevent concurrent progression.
- Added durable Workflow Observability endpoint with step/retry/parallel/outbox metrics.
- Added focused v0.2.33 tests and As-Built documentation.
- Full pytest and PostgreSQL migration execution remain explicitly NOT VERIFIED in the delivery environment.

## v0.2.34 — Phase 1 Scope Lock + Workflow Management UI
- Locked the expanded Phase 1 execution scope in `documents/45_PHASE_1_SCOPE_LOCK_v0.2.34.md`.
- Added backend `GET /api/v1/workflows` tenant-scoped workflow catalog endpoint.
- Added Customer Workflow catalog UI.
- Added Workflow execution/cancellation/observability UI.
- Added Workflow navigation to Customer sidebar.
- Frontend package version bumped to 0.2.34.
- Backend package version bumped to 0.2.34.


## v0.2.47 — OpenTelemetry + Metrics
- Added centralized OpenTelemetry bootstrap with configurable OTLP HTTP export.
- Added FastAPI and SQLAlchemy automatic instrumentation.
- Added manual AI, Employee Run, Workflow, Parallel Branch, Outbox and Celery spans.
- Added Prometheus metrics for HTTP, Workflow, AI usage/cost, Outbox/DLQ, Celery and dependency health.
- Added durable DB-backed queue/run gauges to the Prometheus scrape surface.
- Added Phase 1 observability contract tests and As-Built documentation.
- Full PostgreSQL/Redis/Celery/LM Studio E2E remains NOT VERIFIED unless real services are available.
## v0.5.0 — Phase 5: Document Employee (started ahead of Phase 4 commercial exit gate)

**Governance note**: per `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md`,
Phase 5 was explicitly gated behind Phase 4's commercial exit criterion
(real MRR + minimum paid subscribers), which `documents/62_PHASE4_
MONETIZATION_AS_BUILT_v0.4.2.md` confirms is still "not yet proven". This
release was built at the user's explicit direction, ahead of that gate —
recorded here rather than silently overridden. See
`documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`.

- Added the second specialized AI Employee (`document-employee`) per
  `03_Roadmap_v1.1.docx` §8: PDF/image/DOCX in, extracted text + detected
  fields (dates/amounts/emails/phones/ID candidates) + document-type
  classification (contract/letter/form/administrative_document) out.
- Added the `analyze_document` Tool and `app/services/document_service.py`
  — native PDF text extraction (pypdf) with automatic per-page OCR
  fallback (Tesseract, English + Persian, via pytesseract/pdf2image) for
  scanned pages; direct OCR for images; python-docx for Word documents.
- OCR pipeline actually exercised in the build environment (synthetic
  native-text PDF and OCR-required PNG both correctly routed and
  extracted), not just asserted as implemented.
- Added `scripts/seed_document_employee.py` (idempotent operator seed).
- Extended the existing whitelisted artifact carry-through on
  `Run.output_data` to also recognize `document_artifacts`, alongside the
  existing `report_artifacts` (Phase 2).
- Frontend: generalized the Report Employee's file-picker Run form to also
  cover the Document Employee; added an extracted-text download card on
  the Run detail page.
- Zero new Alembic migrations; Alembic head unchanged at `0a1b2c3d4e5f`.
- Backend test suite: 113 passed in the build environment (103 carried
  over + 10 new in `tests/test_document_service.py`).
- Fixed a pre-existing gap found in the uploaded v0.4.2 package:
  `test_v036_e2e_contract.py` still asserted the Phase 3 Alembic head
  instead of the Phase 4 billing head — corrected alongside the new Phase
  5 head assertion.
- Full PostgreSQL/Redis/Celery/LM Studio E2E for the Document Employee run
  path remains NOT VERIFIED until exercised against real services.

## Release truth
v0.5.0 is the current package baseline (Phase 5 code-complete, started
ahead of the Phase 4 commercial gate per the governance note above). All
prior release-truth statements remain valid for their respective phases.

## v0.4.0 — Phase 3: Validation tooling (+ Phase 2 closed)

- Phase 2 (Report Employee) is now **CLOSED**: the user reported full,
  issue-free testing on a real environment on 2026-08-09. See
  `documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md` "v0.4.0
  update" section for how this user-reported verification is recorded.
- Added Phase 3 ("Validation") tooling per `03_Roadmap_v1.1.docx` §6.
  **Important**: Phase 3 itself is a customer-development outcome (≥3 real
  active customers with recorded feedback) that this codebase cannot
  manufacture — this release only ships the product tooling needed to
  execute and track it. See
  `documents/59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md`.
- Added `feedback` table (new migration `b3c4d5e6f713`, down_revision
  `7a2b3c4d5e6f`) and `POST`/`GET /api/v1/feedback`.
- Added `GET /api/v1/admin/validation` — tracks the Roadmap's own Phase 3
  exit criteria (tenants with a Report Employee Run in the trailing 14
  days, feedback counts/ratings, and an explicit ≥3-tenant check).
- Added the in-product post-Run feedback widget (customer UI) and the
  admin Validation dashboard page.
- Backend test suite: 97 passed in the build environment (91 carried over
  + 6 new); `test_v036_e2e_contract.py` updated for the new Alembic head.
- Alembic head: `7a2b3c4d5e6f` → `b3c4d5e6f713` (one new table, `feedback`;
  no changes to any existing table).

## Release truth
v0.4.0 is the current package baseline (Phase 2 closed, Phase 3 tooling
shipped). v0.3.0 remains the Phase 2 code-complete baseline; v0.2.47
remains the last Phase 1 baseline. Historical As-Built snapshots remain
preserved.

## v0.3.0 — Phase 2: Report Employee

- Added the first specialized AI Employee (`report-employee`) per
  `03_Roadmap_v1.1.docx` §5: CSV/Excel in, KPIs/charts/simple forecast/
  PDF/Excel out.
- Added the `analyze_dataset` Tool and `app/services/report_service.py`
  (pandas/matplotlib/reportlab/openpyxl-based analysis engine).
- Added `GET /api/v1/files/{file_id}/download` — files could previously be
  uploaded and listed but never retrieved; this was a Phase 1 gap closed
  as a direct prerequisite for downloadable reports.
- Added whitelisted `report_artifacts` carry-through from Tool result to
  `Run.output_data` (additive; no other Employee's output shape changes).
- Added `scripts/seed_report_employee.py` (idempotent operator seed).
- Frontend: file-picker Run form and report-artifact download UI for the
  Report Employee; download button on the Files page.
- Zero new Alembic migrations; report artifacts reuse the existing `files`
  table. Alembic head unchanged at `7a2b3c4d5e6f`.
- Backend test suite: 91 passed in the build environment (83 carried over
  + 8 new); `test_tool_registry.py` updated for the new Tool.
- Full PostgreSQL/Redis/Celery/LM Studio E2E for the Report Employee run
  path remains NOT VERIFIED until exercised against real services — see
  `documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.

## Release truth
v0.3.0 is the current package baseline (Phase 2 start). v0.2.47 remains the
last Phase 1 baseline; historical As-Built snapshots remain preserved.

## Schema repair — latest workflow migration reconciliation
- Synchronized the release package with the tested Alembic head `7a2b3c4d5e6f`.
- Preserved the workflow retry migration `fa1b2c3d4e56`.
- Preserved the workflow step timeout/cancellation reconciliation migration `61661b7e79f8`.
- Preserved the workflow approval `created_at` index migration `7a2b3c4d5e6f`.
- Verified exactly one static migration head.
- Verified Python source compilation.
- Release verification records `alembic check` as PASS in the tested environment.


## 0.4.2 — Phase 4 Monetization implementation

- Added Starter / Business / Professional billing plans.
- Added tenant subscription lifecycle and cancellation state.
- Added provider-neutral, idempotent billing event storage.
- Added service-level entitlement/quota enforcement for runs, tokens, employees and workflows.
- Added customer billing endpoints and platform-admin MRR/paid-subscriber reporting.
- Added Phase 4 billing contract tests and as-built documentation.
- Real payment-provider transaction evidence remains the final commercial exit gate.

## 2026-08-11 — B2C Customer Channels

- Added public Customer Channel abstraction for tenant-owned AI Employees.
- Added persistent Customer Conversation and Message models.
- Linked customer conversations to the existing Run execution path.
- Added public chat API with per-conversation customer token isolation.
- Added public chat page and embeddable website widget.
- Added owner-side channel publishing from Employee detail.
- Added B2C customer channel architecture documentation in `docs/current/CUSTOMER_CHANNELS_B2C.md`.

## 2026-08-11 — SaaS Sales Readiness Foundation
- Added tenant-scoped onboarding progress and launch checklist.
- Added Product Catalog with inventory and AI product lookup tools.
- Added commerce integration registry for Shopify/WooCommerce/Magento/custom API/CSV.
- Added Unified Inbox and human handoff state to customer conversations.
- Added frontend pages for onboarding, products, integrations, and inbox.
- Added documentation in `docs/current/SAAS_SALES_READINESS.md`.

## 2026-08-11 — RC3 Customer Operations

- Added tenant-scoped Customer CRM model/API/UI.
- Linked customer profiles to customer conversations.
- Added WhatsApp channel type and provider-neutral inbound webhook foundation.
- Added HMAC webhook signature validation when a channel secret is configured.
- Expanded Unified Inbox with conversation transcript, human replies, takeover and return-to-AI.
- Updated Customer Channels UI to expose WhatsApp as a selectable customer channel.
- Added Customers (CRM) to the Business/AI navigation.
- Added RC3 architecture and production-gap documentation.
- Release rule: every new option/capability must update all relevant dashboards, onboarding, navigation and documentation.

## 1.0.0-rc.4 — Shopify Commerce Loop

- Added Shopify connection test and bounded product/order sync.
- Connected synced products, customers and orders to the tenant catalog/CRM/order domains.
- Added `get_order` and `track_order` AI tools to complement product discovery and order creation.
- Updated Commerce Integrations UI and related product/customer/order refresh behavior.
- Redacted integration secrets from API responses.
- Fixed health endpoint version reporting to match release version.

## 1.0.0-rc.5 — 2026-08-12
- Shopify OAuth installation and GraphQL Admin API connector.
- Shopify webhook HMAC verification, delivery deduplication and reconciliation.
- 14-day tenant trial state and billing entitlements UI.
- Stripe Checkout now carries the configured trial period.
- Integration and Billing dashboards updated with the new options.

## Certification Gates 4–9 Audit Pass (2026-08-12)
- Added fail-closed gate runners for E2E, security, integrations, DR, performance, and final certification.
- Recorded Gate 4–9 evidence and blockers in `docs/audit/PRODUCTION_READINESS_AUDIT_V2_GATES4_9.md`.
- Verified backend compile and frontend contract suite: 127/127 passed.
