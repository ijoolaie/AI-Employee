# Latest Release Verification — As-Built Cumulative Baseline

**Date:** 2026-08-07  
**Status:** Authoritative cumulative verification note

## Purpose

This document records the latest verified runtime state independently of ZIP filename numbering. The package must be treated as cumulative: all previously implemented changes remain part of the baseline unless an explicit change record says otherwise.

## Cumulative implementation carried forward

- Phase 1 RBAC registration and tenant isolation.
- JWT authentication and endpoint permissions.
- Employee / EmployeeVersion / Run execution model.
- Provider-agnostic `AIProvider` interface.
- Provider registry and `AIGateway`.
- LM Studio local provider with OpenAI-compatible API.
- Optional Anthropic provider.
- LM Studio default model: `google/gemma-4-e4b`.
- Gateway-owned token/cost/latency observability.
- Windows Celery `--pool=solo` support.
- Worker-local SQLAlchemy `NullPool` isolation for asyncpg/event-loop safety.
- Prompt + Context Assembly boundary.
- Deterministic JSON serialization of Run input.
- Employee rules in execution context.
- Draft 2020-12 JSON Schema input/output validation.
- Format assertions and local `$ref` support.
- Rejection of external `$ref` / `$dynamicRef`.
- Bounded structured validation errors.
- Schema-definition validation at Employee/version boundaries.
- Audit Log and AI Provider Call persistence.
- Real `.env` exclusion from release archives.

## Latest verified runtime path

The following path has been verified on the Windows development environment:

1. LM Studio server reachable at `http://127.0.0.1:1234/v1`.
2. `google/gemma-4-e4b` available.
3. Standalone LM Studio smoke test: **PASS**.
4. Authenticated `POST /api/v1/runs`: **HTTP 201**.
5. Run initially persisted as `pending`.
6. Celery worker started successfully with `--pool=solo`.
7. Worker connected to Redis and PostgreSQL.
8. Worker loaded the Run and EmployeeVersion.
9. Run transitioned to `running`.
10. AI Gateway called LM Studio through `LMStudioProvider`.
11. LM Studio returned HTTP 200.
12. `ai_provider_calls` row persisted with provider `lm_studio`, model `google/gemma-4-e4b`, token usage and cost `0.0`.
13. `audit_logs` entries persisted for the AI provider call and Run completion.
14. Run output was persisted and Run transitioned to `success`.
15. Transaction committed successfully.
16. Celery task completed successfully.

## Windows asyncpg lifecycle fix

The previously observed:

`AttributeError: 'NoneType' object has no attribute 'send'`

originated from reuse of asyncpg connections across event loops created by `asyncio.run()` inside the Windows Celery worker.

The implemented solution is `worker_db_session()` in `backend/app/core/database.py`:

- creates a worker-local async engine;
- uses SQLAlchemy `NullPool`;
- creates a worker-local session factory;
- disposes the engine after each task.

The API continues using the normal pooled async engine. This separation is intentional.

## Verification boundaries

### Verified

- Source structure and cumulative implementation present.
- LM Studio provider and registry.
- Gateway integration.
- Celery worker execution.
- PostgreSQL persistence.
- Redis/Celery transport.
- Run success path.
- AI Provider Call persistence.
- Audit Log persistence.
- Local cost accounting.
- Schema-validation focused tests: 10 passed.

### Environment-dependent

- Full pytest requires all packages from `backend/requirements.txt` to be installed.
- Real `.env` values are intentionally not shipped.
- Anthropic live calls require a real API key and are not required for the local LM Studio baseline.

## Long-term architecture remains unchanged

The current local LM Studio path is an implementation choice, not an architectural replacement for the planned multi-provider AI Core. Future providers, Tool Registry, RAG, Memory, Workflow, Human Approval, quotas, billing and integrations must continue to enter through their documented provider/service boundaries.

## Release policy

- No real `.env` in ZIP.
- No API keys or credentials in source.
- `.env.example` is the only environment template shipped.
- This document is the authoritative latest verification note when ZIP numbering and historical filenames differ.

## v0.2.17 Usage/Cost reporting addition

The cumulative baseline now includes a read-only tenant-scoped Usage/Cost reporting surface derived from existing `ai_provider_calls` records. `GET /api/v1/usage/summary` reports calls, success/failure, token totals, recorded cost, average latency and provider/model breakdown. The Customer Panel exposes the same information at `/usage`. No migration is required and no raw provider responses or secrets are exposed. Billing, quotas and invoicing remain separate planned capabilities.


## v0.2.18 verification addendum

- Tool Registry source compilation: PASS.
- Focused Tool Registry/provider tests: 6 PASS.
- No database migration introduced.
- Real `.env` excluded from release package.
- Tool execution is limited to registered, schema-validated, side-effect-free built-ins in this release.


## v0.2.24 verification addendum — RAG runtime context integration

- Knowledge Base retrieval is now connected to actual Employee Run execution.
- RAG is opt-in per EmployeeVersion and requires explicit `query_fields`; `top_k` is bounded to 1–20.
- Retrieval is tenant-scoped and restricted to indexed documents with active source files.
- Retrieved content enters `ExecutionContext.retrieved_context` and then Prompt + Context Assembly v2 before the AI Gateway.
- Retrieved content is explicitly marked as untrusted reference material.
- `knowledge.retrieved` audit events and RAG provider-call metadata are recorded.
- Human Approval waiting Runs no longer receive `completed_at` when execution pauses.
- Focused RAG/context tests: **9 passed** in the release verification environment.
- Full project runtime verification remains dependent on the target environment's installed dependencies and live PostgreSQL/Redis/LM Studio services.

## v0.2.27 Release Verification Addendum

Memory lifecycle/versioning is now implemented: active memories may be superseded into versioned historical records; expiry is enforced before retrieval; explicit conflict keys and extractor subject keys support deterministic conflict handling. Repository-wide pytest remains environment-dependent when required Python runtime dependencies are absent.
