# Real-Model Verification — v0.6.1

## Purpose
This document records the outcome of running the platform's AI Gateway
and the Document/Report Employee scenarios against a **real** local LLM
(LM Studio), as opposed to the mocked/monkeypatched provider tests that
had shipped in every prior package (including v0.6.0).

## Status and attribution (read before relying on this)
Everything in this document is **user-reported**, per the same
convention already used elsewhere in this project (see, e.g.,
`23_AS_BUILT_CURRENT_STATE_v0.6.0.md`, "`real_postgresql_redis_celery_e2e`:
`VERIFIED_USER_REPORTED_2026-08-09`"). The delivery/build environment that
produced this package has no network egress and cannot reach an LM
Studio instance, so **none of this was independently executed by the
assistant in this environment.** It is recorded here because the project
owner ran it and reported the results, not because it was re-verified
here.

## What was reported as run, against a real model

### 1. `backend/tests/test_ai_providers.py`, executed against a real LM Studio model
- The provider-abstraction test suite was re-run outside this delivery
  environment against a live LM Studio server (not the `FakeClient`/
  `monkeypatch` doubles used when this suite runs inside the build
  sandbox).
- Reported result: **all tests passed** against the real model.
- This exercises `LMStudioProvider` end-to-end: request shaping, the
  OpenAI-compatible response mapping, token accounting, and
  `get_default_provider()` returning the LM Studio provider by default.

### 2. Document Employee and Report Employee, real-stack E2E with a real model
- Runs were executed against the live stack (per the `DEV_SETUP.md`
  "Quick manual check" steps for v0.3.0 and v0.5.0) with the AI Gateway
  pointed at a real LM Studio model rather than a mock.
- Reported result: **passed** — both Employees completed Runs and
  produced their respective downloads (Report Employee: PDF/Excel/chart;
  Document Employee: extracted text, including the OCR fallback path).
- This is the first real-model confirmation of
  `document_employee_real_stack_e2e` and `document_employee_seed_script`,
  which `23_AS_BUILT_CURRENT_STATE_v0.6.0.md` had listed as
  `NOT_VERIFIED_no_live_services_no_user_report_yet`.

## What was explicitly deferred, at the project owner's direction
- **`AnthropicProvider` was not tested against the real Anthropic API.**
  `backend/app/ai/providers/anthropic_provider.py` exists in the codebase
  (provider-abstraction support was built multi-provider from Phase 1),
  but no real-model run was made against it in this round, and none is
  required right now. This is a deliberate scope decision by the project
  owner, not a gap discovered by accident — noted here so it isn't later
  mistaken for a completed check.
- No other provider (OpenAI, etc.) exists in this codebase yet — only
  `lm_studio_provider.py` and `anthropic_provider.py` are implemented, so
  "real-model verification" in this release means LM Studio only.

## What this does and does not close
- This closes the "not yet exercised against a live stack" caveat that
  `63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md` and
  `23_AS_BUILT_CURRENT_STATE_v0.6.0.md` had carried for Phase 5, and adds
  a first real-model (as opposed to mocked) pass for the AI Gateway
  provider tests.
- It does **not** touch the still-open Phase 4 commercial exit gate (real
  Stripe run) or `feedback_and_validation_dashboard_e2e` — those remain
  as documented in `64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md` and
  `23_AS_BUILT_CURRENT_STATE_v0.6.0.md`.
- It does not constitute testing of the Anthropic provider path; treat
  that path as unverified until it is explicitly tested.

## Manifest/status updates in this release
See `PROJECT_FILE_MANIFEST.json` → `verification_status` for the new
`real_llm_model_e2e_*` and `anthropic_provider_real_model_test` keys, and
`23_AS_BUILT_CURRENT_STATE_v0.6.1.md` for the consolidated current state.
