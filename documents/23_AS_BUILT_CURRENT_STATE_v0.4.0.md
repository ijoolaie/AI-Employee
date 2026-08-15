# AS-BUILT CURRENT STATE — v0.4.0

## Phase 1 (cumulative, unchanged)
See `23_AS_BUILT_CURRENT_STATE_v0.2.47.md` for the full Phase 1 baseline.
Nothing in Phase 1 was removed or behaviorally changed by v0.3.0 or v0.4.0.

## Phase 2 (cumulative) — CLOSED
Report Employee: `analyze_dataset` Tool, `report_service.py` analysis
engine, `report-employee` System Employee, `GET /files/{id}/download`,
`report_artifacts` carry-through, matching frontend UI. **Closed** per the
user-reported real-environment test on 2026-08-09 (see
`58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`, "v0.4.0 update" section).
Full detail: `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.

## Phase 3 additions (this release) — tooling only, NOT a completion claim
- Added `feedback` table + `POST`/`GET /api/v1/feedback`.
- Added `GET /api/v1/admin/validation` — Phase 3 exit-criteria tracking
  (≥3 tenants regularly running the Report Employee + recorded feedback).
- Added the in-product post-Run feedback widget and the admin Validation
  dashboard page.
- Full detail, including the important scoping note that Phase 3 itself is
  a customer-development outcome this codebase cannot manufacture:
  `59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md`.

## Verification boundary
- Python compile/static checks: PASS for all v0.3.0 + v0.4.0 additions.
- Backend test suite: 97 passed in this build environment (91 carried over
  + 6 new in `tests/test_feedback_schema.py`). Two pre-existing tests were
  updated across the two releases to reflect real, intentional changes:
  `test_tool_registry.py` (new Tool) and `test_v036_e2e_contract.py` (new
  Alembic head).
- Static Alembic head analysis: exactly one head, `b3c4d5e6f713`.
- Report Employee real-environment E2E: user-reported VERIFIED,
  2026-08-09.
- Feedback/Validation-dashboard real-environment E2E: NOT VERIFIED yet —
  this is new in v0.4.0 and has not been run against a live database by
  anyone, including the user, as of this document.
- Frontend production build: NOT VERIFIED in this delivery environment (no
  `node_modules`).

## Where the project stands against the Roadmap
- Phase 0 (Foundation): documented/agreed, per Phase 1 baseline docs.
- Phase 1 (Core): CLOSED, per `23_AS_BUILT_CURRENT_STATE_v0.2.47.md`.
- Phase 2 (Report Employee): CLOSED, per the above.
- Phase 3 (Validation): tooling to execute and track it is now
  IMPLEMENTED and shipped; **the phase itself (3–5 real active customers
  with recorded feedback) has not started/completed inside this
  codebase** — that is a business execution step for the team, using the
  tools this release provides. Do not mark Phase 3 "done" in future
  documents without real tenant data in `/admin/validation` and read,
  qualitative feedback behind it.
- Phase 4 (Monetization) and Phases 5–8 (Document/Invoice/Order/Sales
  Employees): unchanged, still future work per the Roadmap.

## Runtime verification addendum — 2026-08-09

The workflow runtime/outbox implementation was additionally verified against the
real Docker stack used for development (`postgres:16-alpine`, `redis:7-alpine`,
Celery Worker and Celery Beat).

### Verified Outbox → Celery → Workflow path

Three real `workflow.execute` Outbox messages were observed in PostgreSQL with
`status=dispatched` and `attempts=1`. Their payloads referenced three distinct
Workflow Runs. The Celery Worker received all three `workflow.execute` tasks and
reported them as successful.

The corresponding Workflow Runs were all persisted as `success`, and each had
its `hello` WorkflowStepRun persisted as `success`.

### Outbox lifecycle clarification

The Outbox dispatcher uses two intentionally different completion boundaries:

- `workflow.execute`, `workflow.event_dispatch`, and `workflow.parallel_branch`
  are considered dispatched once Celery accepts the task; the Outbox row is then
  marked `dispatched`.
- `email.send` remains `processing` after the dispatcher hands it to Celery. The
  SMTP worker owns the final `mark_dispatched()` transition because the durable
  side effect has not happened at enqueue time.

The email handoff span now explicitly records `outbox.status=queued` so this
intentional lifecycle distinction is visible in telemetry.

### Verification evidence

- PostgreSQL connection verified with the configured `aiep` role/database.
- Celery Worker registration verified for `outbox.dispatch`, `workflow.execute`,
  `workflow.event_dispatch`, `workflow.parallel_branch`, schedule, approval
  expiry, timeout sweep, and email tasks.
- Three real workflow executions verified end-to-end on 2026-08-09.
- Added `tests/test_v041_outbox_hardening.py` for the dispatch/telemetry contract.
- Local full pytest collection in the packaging environment is currently blocked
  by missing optional runtime dependencies (`asyncpg` and `python-jose`); this is
  an environment limitation, not a newly observed application failure.


## RELEASE v0.4.1 — OUTBOX HARDENING + VERSION SYNCHRONIZATION — 2026-08-09

The v0.4.1 baseline retains all v0.4.0 behavior and adds Outbox observability hardening plus release-version synchronization. Workflow Outbox messages are marked `dispatched` after Celery accepts them; email handoff remains `processing` until the email worker completes the durable SMTP side effect. The email handoff span records `outbox.status=queued`. Backend package metadata, FastAPI metadata, health endpoints and frontend package metadata are aligned to `0.4.1`.

The Roadmap's Phase 4 (Monetization) remains future work: the current Usage surface is reporting-only and there is no subscription, invoicing, payment, quota-enforcement or upgrade flow. Consequently this release must not be interpreted as completion of Roadmap Phase 4.

Definitive v0.4.1 release details: `documents/60_RELEASE_0.4.1_OUTBOX_HARDENING_AS_BUILT.md`.
