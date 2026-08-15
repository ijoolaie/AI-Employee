# As-Built Baseline — v0.2.12-LMSTUDIO

**Date:** 2026-08-07

This document is the authoritative **current implementation baseline** for release v0.2.12-LMSTUDIO. The long-term Product Vision, Master Plan and Roadmap remain authoritative for planned scope; this document records what is actually built and verified in this package.

## 1. Planned long-term architecture

The platform remains a multi-tenant AI Employee SaaS with Customer/Super Admin/Developer interfaces, Employee versioning, provider-agnostic AI Gateway, RAG, Tools, Workflow, Integrations, Usage/Billing, Analytics, auditability, replayability and bilingual Persian/English UX.

The architecture intentionally keeps Employee input/output contracts as JSON Schemas so future Validation, Tool, Workflow and Human Approval layers can reuse the same contract boundary.

## 2. As-Built inherited from v0.2.11

- FastAPI + PostgreSQL + Redis + Celery backend.
- JWT authentication, tenant isolation and Phase 1 RBAC.
- Employee + immutable EmployeeVersion + Run execution model.
- Provider-agnostic `AIProvider` interface, registry and `AIGateway`.
- LM Studio is the default development provider.
- Default model: `google/gemma-4-e4b`.
- Default endpoint: `http://127.0.0.1:1234/v1`.
- Anthropic remains an optional provider and requires an API key.
- AI Provider Calls record provider, model, token usage, cost, latency and status.
- Local LM Studio inference cost is `0.0 USD`.
- Windows Celery development mode is `--pool=solo`.
- Celery worker DB sessions use a worker-local SQLAlchemy async engine with `NullPool` to avoid Windows `asyncio.run()`/asyncpg connection-loop reuse failures.
- Real `.env` files are excluded from release packages; `.env.example` is included.
- Gateway latency and cost are single-source Gateway-owned observability values.

## 3. v0.2.12 implementation delta — JSON Schema Validation

### Input validation

`app/services/run_service.py` now validates the complete Run `input_data` object against the current `EmployeeVersion.input_schema` using Draft 2020-12 JSON Schema validation.

This replaces the previous placeholder that only checked the `required` array.

Validation now covers, where declared by the Employee schema:

- required properties
- property types
- additional properties
- string/number/array/object constraints
- nested structures
- enums and other standard Draft 2020-12 constraints

An invalid input is rejected before a Run row is created and returns the standard application validation error (`422`).

### Output validation

After the AI Gateway returns successfully, the Run service constructs the canonical output payload:

```json
{"text": "<model response>"}
```

That payload is validated against `EmployeeVersion.output_schema` before the Run can become `success`.

If output validation fails:

- the Run becomes `failed`;
- provider token usage and Gateway cost remain preserved on the Run;
- the validation error is stored in `Run.error`;
- the existing `run.completed` audit path records failure;
- the Celery worker commits the failure state.

The AI Provider Call itself remains recorded as successful because model execution succeeded; the failure is specifically an Employee output-contract failure.

### Schema-definition validation

Employee creation and new EmployeeVersion publication now validate `input_schema` and `output_schema` themselves using Draft 2020-12 schema checks. Invalid schema definitions are rejected before being persisted.

## 4. New validation module

Added:

`backend/app/services/schema_validation.py`

Responsibilities:

- validate JSON Schema definitions;
- validate runtime data against a schema;
- produce bounded, structured validation details (`field`, `path`, `validator`, `message`);
- preserve the existing `ValidationAppError` contract.

The module is deliberately independent of the AI provider so validation remains provider-agnostic.

## 5. Test coverage added

Added `backend/tests/test_schema_validation.py` covering:

- valid input payloads;
- wrong input types;
- missing required fields;
- output payload validation;
- unconstrained empty schemas;
- invalid JSON Schema definitions.

The existing LM Studio/provider tests remain part of the package.

## 6. Verified / test environment notes

- Source compilation: **PASS**.
- New JSON Schema validation tests: **PASS**.
- Combined provider + schema test collection in the packaging environment is partially blocked by missing preinstalled backend dependencies (`asyncpg`/`python-jose`); this is an environment limitation, not a source failure.
- The user's Windows environment remains the authoritative runtime verification environment for PostgreSQL, Redis, Celery and LM Studio E2E.

## 7. Release/secrets policy

The real `.env` is intentionally **not** included in the ZIP. Only `.env.example` is shipped. Local configuration may contain secrets and machine-specific endpoints and must remain outside release archives.

## 8. Next planned implementation steps

1. Expand Run integration tests against a real/test PostgreSQL environment.
2. Add structured Tool execution and Tool-result validation behind the AI Gateway.
3. Add Context/RAG assembly while preserving provider agnosticism.
4. Implement Human Approval / `waiting` Run state.
5. Add quota/rule enforcement and usage aggregation.
6. Continue toward Workflow Engine, Integrations, Billing and Phase 2 UX/i18n according to the long-term roadmap.
