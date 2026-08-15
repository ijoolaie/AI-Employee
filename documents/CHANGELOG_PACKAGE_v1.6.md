# Change Log Package v1.6 — Latest Cumulative LMSTUDIO Baseline

**Date:** 2026-08-07

This package preserves the complete cumulative implementation through the hardened JSON Schema Validation layer and records the latest real Windows LM Studio/Celery/PostgreSQL end-to-end verification.

## Current cumulative state

The current implementation includes all previously recorded changes from the RBAC baseline through:

- provider-agnostic AI Gateway;
- LM Studio provider and registry;
- Windows Celery/asyncpg lifecycle isolation;
- Gateway latency and single-source cost accounting;
- Prompt + Context Assembly;
- Draft 2020-12 JSON Schema validation;
- format assertions, local references and external-reference rejection;
- bounded structured validation errors;
- Audit Log / AI Provider Call persistence;
- verified local LM Studio Run execution.

## Latest verification

- LM Studio smoke test: **PASS**
- Authenticated `POST /api/v1/runs`: **201**
- Celery Windows `--pool=solo`: **PASS**
- PostgreSQL worker access: **PASS**
- LM Studio completion: **HTTP 200**
- AI Provider Call persistence: **PASS**
- Audit Log persistence: **PASS**
- Run output/token persistence: **PASS**
- Local LM Studio cost: **0.0 USD**
- Celery task completion: **PASS**
- Focused schema validation suite: **10 passed**

## Important lifecycle correction

The Windows asyncpg `NoneType.send` failure is handled by `worker_db_session()` with a worker-local SQLAlchemy `NullPool`. This is required for Celery tasks that create and close event loops with `asyncio.run()` and must not be removed.

## Secrets

Real `.env` files remain excluded from all release packages. Only `.env.example` is shipped.

## v0.2.26 As-Built Addendum
Automatic Employee Memory Extraction & Consolidation implemented and documented. See `33_AUTOMATIC_MEMORY_EXTRACTION_AS_BUILT_v0.2.26.md`.

## Release synchronization — v0.2.28
Workflow Engine foundation added: versioned manual workflows, linear Employee actions, context propagation, durable workflow state, retries and workflow RBAC.
