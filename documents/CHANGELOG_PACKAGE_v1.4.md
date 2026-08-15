# AI Employee Platform — Documentation Package Changelog

## v1.4 — 2026-08-06

### Summary

- Locked **bilingual requirement** (Persian + English, RTL for `fa`) as a construction document for Phase 2 execution.
- Frontend client harden: richer API error messages, session-expiry redirect to login.
- Backend integration verified on Windows (Auth, Employees, Runs+Celery, Files).

### Changes

| Document | Change |
|----------|--------|
| **22_I18n_Localization_v1.0** | **New** — mandatory fa/en i18n, RTL, Phase 2 acceptance criteria |
| **08_Frontend** | Bumped notes to **v1.3** — references doc 22; i18n no longer "optional someday" |
| **CHANGELOG_PACKAGE** | This file (v1.4) |

### Implementation note (not full i18n yet)

Customer Panel MVP remains primarily English UI in v0.1.x. Full message catalogs + language switcher + RTL layout ship in **Phase 2** per document 22. Product decision is binding from v1.4 docs onward.

### Companion code

- Frontend: improved `getErrorMessage`, 401 → `/login?reason=session`
- Backend: unchanged for the v1.4 i18n package bump; subsequent 2026-08-07 LM Studio integration is documented below

---

*End of package changelog v1.4*


## AI Core / LM Studio integration — 2026-08-07

- Added `LMStudioProvider` using LM Studio's OpenAI-compatible `/v1/chat/completions` endpoint.
- Added `app.ai.providers.registry` for provider selection; `AIGateway` remains provider-agnostic.
- Development defaults: `lm_studio` + `google/gemma-4-e4b` at `http://127.0.0.1:1234/v1`.
- Local inference cost is recorded as `0.0 USD`; latency and model-reported token usage are still recorded.
- Anthropic remains supported as an optional provider.
- No API key is required for the default local LM Studio path unless the LM Studio server is configured to require one.


## v1.5 — 2026-08-07 — As-Built baseline + LM Studio

### Summary

- The documentation package now explicitly separates **Planned**, **As-Built**, and **Verified** state.
- Added `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` as the current-state reference.
- Synchronized all primary DOCX documents with an As-Built appendix without rewriting their historical design intent.
- LM Studio is the default development AI provider; Anthropic is optional.
- Real `.env` files are intentionally excluded from release packages.
- Windows Celery development mode is documented as `--pool=solo`.

### Verification note

The codebase compiles successfully. Full pytest execution in the packaging environment is currently blocked by a missing `python-jose` dependency. In the user's Windows environment, Celery successfully connects to Redis and executes `run.execute`; the previously observed Anthropic failure was persisted through the Run, AI Provider Call, and Audit Log paths. A successful Gemma/LM Studio E2E run remains an explicit verification step.


## v1.6 — 2026-08-07 — Current As-Built synchronization

- Backend release is now `v0.2.9-LMSTUDIO`.
- Synchronized the documentation set with the distinction between Planned, As-Built and Verified.
- Added provider tests and a direct LM Studio verification script.
- Confirmed Windows Celery development mode as `--pool=solo`.
- Kept the real `.env` outside release packages.
- LM Studio/Gemma E2E remains explicitly pending until executed in the user's local environment.

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.



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

- Run input/output contracts now use Draft 2020-12 JSON Schema validation.
- Employee schema definitions are validated at create/version-publish time.
- Validation failures use the standard application error contract and preserve Run usage/cost on output-contract failures.
- Current-state baseline: `documents/00_AS_BUILT_BASELINE_v0.2.12_LMSTUDIO.md`.
