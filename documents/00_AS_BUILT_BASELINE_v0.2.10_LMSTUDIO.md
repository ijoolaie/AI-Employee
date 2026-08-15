# AI Employee Platform — As-Built Baseline

**Baseline:** v0.2.10-LMSTUDIO  
**Date:** 2026-08-07  
**Scope:** Phase 1 / Step 01 + local-first AI provider integration

## 1. Authority and purpose

این سند مرجع وضعیت واقعی بسته نرم‌افزاری در این Release است. Master Plan / Product Vision / Roadmap وضعیت هدف و مسیر بلندمدت را تعریف می‌کنند؛ این سند وضعیت **As-Built** را ثبت می‌کند. وضعیت **Verified** فقط برای مواردی ثبت می‌شود که واقعاً در محیط اجرا مشاهده شده‌اند.

## 2. Long-term target — Planned

هدف بلندمدت همان معماری SaaS چندمستأجری AI Employee Platform است: Core مستقل از کانال، Employeeهای نسخه‌بندی‌شده، RAG/Knowledge Base، Tools، Workflow، چند Provider، Billing/Usage، Analytics، پنل مشتری، Super Admin، Developer Console، Integrations و i18n فارسی/انگلیسی. این‌ها برنامه بلندمدت‌اند و نباید صرفاً به‌دلیل وجودشان در اسناد، قابلیت فعلی تلقی شوند.

## 3. As-Built architecture

```text
Client / Frontend
       |
       v
FastAPI API Layer
       |
       +--> Auth / JWT / Tenant Context / RBAC
       +--> Employees / Employee Versions
       +--> Files
       +--> Runs
       |       |
       |       v
       |   Redis -> Celery worker
       |       |
       |       v
       |   Run Service -> AI Gateway -> Provider Registry
       |                              |
       |                 +------------+------------+
       |                 |                         |
       |            LM Studio                 Anthropic
       |            (default dev)             (optional)
       |                 |
       |          OpenAI-compatible API
       |
       +--> Audit Log / AI Provider Calls
       |
       v
PostgreSQL
```

## 4. AI provider implementation

- `AIProvider` is the provider-agnostic contract.
- `AIGateway` is the single entry point for model calls and records provider, model, latency, token usage, cost, status and audit information.
- `app.ai.providers.registry` selects the provider from `AI_DEFAULT_PROVIDER`; the Gateway does not directly import a concrete provider.
- `LMStudioProvider` uses LM Studio's OpenAI-compatible `POST /v1/chat/completions`.
- Development defaults: `lm_studio`, model `google/gemma-4-e4b`, base URL `http://127.0.0.1:1234/v1`.
- Local inference cost is `0.0 USD`; prompt/completion token counts remain observable when LM Studio reports usage.
- Anthropic remains an optional provider and requires `ANTHROPIC_API_KEY`.

## 5. Environment and secrets

The real `.env` is intentionally excluded from every ZIP/release package. Only `.env.example` is shipped. This is a permanent release policy, not an omission. Developers create `.env` locally.

For the current local-first path:

```env
AI_DEFAULT_PROVIDER=lm_studio
AI_DEFAULT_MODEL=google/gemma-4-e4b
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=
```

No Anthropic key is required for LM Studio development.

## 6. Windows/Celery As-Built decision

The default Celery prefork pool produced the observed billiard failure:

`ValueError: not enough values to unpack (expected 3, got 0)`

The supported Windows development command is therefore:

```powershell
celery -A app.workers.celery_app:celery_app worker -l info --pool=solo
```

The worker successfully connected to Redis and advertised `run.execute`.

## 7. Verified state

### Verified
1. `POST /api/v1/runs` returned HTTP `201` and created a Run with `pending` status.
2. Celery received `run.execute` on Windows using `--pool=solo`.
3. The worker loaded the Run and EmployeeVersion from PostgreSQL and transitioned the Run to `running`.
4. `ai_provider_calls`, `audit_logs`, and `runs.error` were populated correctly when the selected provider failed.
5. The previous Anthropic test failed for the expected reason: no `ANTHROPIC_API_KEY`; the failure path was persisted correctly.

### Pending verification
- A successful end-to-end Gemma call through LM Studio, followed by a successful `POST /api/v1/runs` execution, must still be run in the user's Windows environment.

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

## 8. Current implementation limits

- Provider routing/failover policy is not yet a production multi-provider strategy.
- Output JSON Schema enforcement remains pending.
- Tenant quota/rules remain pending.
- Full RAG, Tool runtime, Human Approval and Workflow Engine remain future work.
- Billing, subscription automation, production secret management and horizontal scaling remain future work.
- Full bilingual UI is a locked Phase 2 requirement, not a current implementation claim.

## 9. Release documentation rule

Every release document must distinguish: **Planned → As-Built → Verified**. Historical design documents are not rewritten to pretend that future capabilities already exist; instead, this current-state appendix is synchronized into them.

## 10. Release delta from v0.2.8-LMSTUDIO

- Backend package version bumped to `0.2.9`.
- Added provider-focused automated tests.
- Added `backend/scripts/verify_lm_studio.py` for direct local endpoint verification.
- Updated README, local development instructions and package manifest.
- Synchronized the documentation set with the current As-Built/Verified status.
- Preserved the no-real-`.env` release policy.
