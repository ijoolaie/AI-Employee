# AI Employee Platform — As-Built Baseline v0.2.17 (LM Studio)

**Date:** 2026-08-07  
**Baseline policy:** cumulative; this release carries forward all implemented v0.2.7–v0.2.15 changes plus the v0.2.17 Usage/Cost reporting surface.

## Current architecture

The platform remains a multi-tenant AI Employee SaaS with RBAC, versioned Employees, provider-agnostic AI Gateway, local-first LM Studio execution, deterministic Prompt/Context Assembly, JSON Schema validation, auditability and Run Trace.

The long-term architecture still includes Tools, RAG/Knowledge Base, Memory, Workflow, Human Approval, quotas, Billing, Analytics, Integrations, multi-provider routing and expanded UX. Those planned capabilities are not represented as implemented merely because they appear in the master documents.

## Cumulative implemented capabilities

- RBAC registration and tenant isolation.
- JWT authentication and endpoint permissions.
- Employee / EmployeeVersion / Run model.
- Provider-agnostic AIProvider interface.
- Provider registry.
- LM Studio provider and optional Anthropic provider.
- `google/gemma-4-e4b` local development model.
- Gateway-owned latency, token and cost accounting.
- Windows Celery `--pool=solo` support.
- Worker-local SQLAlchemy `NullPool` for asyncpg event-loop isolation.
- Deterministic Prompt/Context Assembly.
- Employee rules as execution context.
- Draft 2020-12 JSON Schema input/output validation.
- Hardened validation with format assertions, local `$ref` support and external reference rejection.
- Audit Log and AI Provider Call persistence.
- Run Trace API and Customer Run Trace timeline.
- Real Windows LM Studio/Celery/PostgreSQL E2E verification.
- **v0.2.17:** tenant-scoped read-only Usage/Cost summary API and Customer Usage page.

## v0.2.17 Usage surface

`GET /api/v1/usage/summary`

Reports existing AI Provider Call records by tenant and optional time range. It exposes call counts, success/failure counts, token totals, recorded cost, average latency and provider/model breakdown.

Customer route:

`/usage`

No new database tables or migrations were introduced.

## Verified local runtime path

`Auth → POST /runs (201) → pending → Celery --pool=solo → worker-local DB session → Prompt/Context Assembly → AIGateway → LM Studio/Gemma → AI Provider Call + Audit Log → Run success → COMMIT`

The LM Studio smoke test and the real Gemma/Celery/PostgreSQL Run path were previously verified in the user's Windows environment.

## Security / release policy

- Real `.env` files are excluded from release archives.
- Only `.env.example` is shipped.
- No provider credentials are stored in the package.
- Usage reporting is tenant-scoped and does not expose provider raw responses.

## Next implementation priorities

1. Structured Tool Registry and Tool execution behind the AI Gateway.
2. RAG / Knowledge retrieval and context injection.
3. Human Approval / `waiting` Run state.
4. Quota/rule enforcement using the now-available usage data.
5. Billing/invoicing and workflow-level attribution.
6. Workflow Engine and Integrations.
