# Current As-Built Addendum — v0.2.10-LMSTUDIO

**Date:** 2026-08-07

This addendum is authoritative for the current implementation state. The long-term Product Vision, Master Plan and Roadmap remain authoritative for future scope.

## Planned

The platform remains a multi-tenant AI Employee SaaS with Customer/Super Admin/Developer interfaces, Employee versioning, AI Gateway, RAG, Tools, Workflow, Integrations, Usage/Billing, Analytics and bilingual Persian/English UX.

## As-Built in v0.2.10

- FastAPI + PostgreSQL + Redis + Celery backend.
- JWT authentication, tenant isolation and Phase 1 RBAC.
- Employee + immutable EmployeeVersion + Run execution model.
- AIProvider abstraction + AIGateway + provider registry.
- LM Studio is the default development provider.
- Default model: `google/gemma-4-e4b`.
- Default endpoint: `http://127.0.0.1:1234/v1`.
- Anthropic is optional and requires an API key.
- AI provider calls record latency, tokens, cost and status.
- Local LM Studio cost is `0.0 USD`.
- Windows Celery development mode is `--pool=solo`.
- Real `.env` is excluded from releases; `.env.example` is included.
- Provider tests and a direct LM Studio smoke-test script are included.

## Verified

- Run creation: HTTP 201.
- Celery/Redis worker connectivity: PASS.
- Run loading and state transition to `running`: PASS.
- Error persistence/audit path: PASS.
- Anthropic missing-key failure path: PASS.

## Pending verification

- Successful LM Studio/Gemma end-to-end Run after the asyncpg worker-session fix in the user's local Windows environment.

## Windows Celery / asyncpg lifecycle fix

During the first real LM Studio end-to-end attempt, the Run reached the Celery worker and PostgreSQL access, but the worker failed with:

```text
AttributeError: 'NoneType' object has no attribute 'send'
```

The traceback originated in Windows `asyncio.proactor_events` while `asyncpg` was writing through a connection. The cause is the interaction between `asyncio.run()` (a new event loop per Celery task) and a reusable SQLAlchemy async connection pool.

The As-Built fix is now implemented in `app.core.database.worker_db_session()`: Celery Run execution uses a worker-local async engine with SQLAlchemy `NullPool`, and the engine is disposed after each task session. The API keeps its normal pooled engine. This is an infrastructure/lifecycle fix only; the AI Gateway and LM Studio provider contract are unchanged.

### Verification status after the fix

- Fix implemented: **PASS (source-level)**
- Source compilation/restart after fix: **PENDING**
- Successful LM Studio/Gemma Run after fix: **PENDING**

## Next technical step

1. Ensure LM Studio is serving `google/gemma-4-e4b`.
2. Run `python backend/scripts/verify_lm_studio.py` from the backend environment.
3. Keep API + PostgreSQL + Redis + Celery `--pool=solo` running.
4. Re-run `POST /api/v1/runs`.
5. Confirm Run reaches `success`, `output_data.text` is populated, and `ai_provider_calls` shows provider `lm_studio` with cost `0.0`.
