# AS-BUILT CURRENT STATE — v0.6.1

## What changed since v0.6.0
This is a verification/documentation update, not a feature release:
- Real-model (LM Studio) verification of the AI Gateway and of Phase 5
  (Document Employee) was run and reported by the project owner — see
  `65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md` for exactly what was
  and wasn't covered, including the explicit decision to defer testing
  the Anthropic provider.
- Phase 7 (Invoice Employee) is scope-locked and the Roadmap's Employee
  numbering is formally reconciled — see
  `66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`. No Phase 7 code
  exists yet.
- Version strings realigned to `0.6.1` across `backend/pyproject.toml`,
  `frontend/package.json`, `backend/app/main.py` (the FastAPI `version=`
  kwarg and both health-check endpoints, which had been left at a stale
  `0.4.2` since before the v0.6.0 package).

## Governance note (read first)
Per `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, further roadmap phases
were recommended to wait until Phase 4's commercial exit gate was closed.
Phase 5 (Document Employee) was built ahead of that gate at explicit user
direction, and v0.6.0 (Stripe adapter) closed the implementation half of
that gate. The user has now directed the project to proceed to Phase 7
(Invoice Employee, see the numbering note below) rather than wait for the
commercial half of the gate (a real Stripe run). The commercial gate
remains open.

## Phase 1 (cumulative, unchanged)
See `23_AS_BUILT_CURRENT_STATE_v0.2.47.md`.

## Phase 2 (cumulative) — CLOSED
Report Employee. See `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.

## Phase 3 (cumulative) — tooling shipped
Validation feedback/dashboard tooling. See
`59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md`.

## Phase 4 (cumulative) — implementation complete, commercial proof still pending
Billing plans/subscriptions/entitlements/MRR reporting (provider-neutral
core) plus a real Stripe adapter. See
`62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md`,
`61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, and
`64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`.

## Phase 5 (cumulative) — Document Employee
Code-complete since `v0.5.0`. As of this document, a real-model E2E pass
against a live stack has been **user-reported** (see
`65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`) — this supersedes the
"not exercised against a live stack" caveat carried in
`23_AS_BUILT_CURRENT_STATE_v0.6.0.md`. It was not independently re-run in
this delivery environment (no live-stack or LM Studio network access
here).

## Phase 6 (cumulative) — Stripe payment-provider adapter
Unchanged from `v0.6.0`. See
`64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`. Real Stripe API calls
remain unverified from any delivery environment used so far.

## Phase 7 — Invoice Employee: SCOPE-LOCKED, not yet implemented
See `66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`. This is the next
work item.

## Verification boundary (this document)
- Backend test suite: still 121 tests, no test count change in this
  release (documentation/version-string only).
- New real-model verification (LM Studio), **user-reported, not
  re-executed in this environment**:
  - `test_ai_providers.py` against a real LM Studio model: reported PASS.
  - Document Employee and Report Employee real-stack E2E against a real
    LM Studio model: reported PASS.
  - Anthropic provider real-model test: explicitly **deferred**, not
    run, per user direction — do not treat as verified.
- Stripe-related verification boundary unchanged from `v0.6.0`.

## Where the project stands against the Roadmap
- Phase 0 (Foundation): documented/agreed.
- Phase 1 (Core): CLOSED.
- Phase 2 (Report Employee): CLOSED (user-reported, 2026-08-09).
- Phase 3 (Validation): tooling shipped; phase itself not independently
  confirmed complete.
- Phase 4 (Monetization): implementation CLOSED; commercial exit gate
  (proven real MRR + minimum paid subscribers) remains open.
- Phase 5 (Document Employee): code-complete; real-model E2E
  user-reported PASS (this document).
- Phase 6 (real payment provider): code-level IMPLEMENTED and
  unit-tested; live Stripe verification pending.
- Phase 7 (Invoice Employee): SCOPE-LOCKED (this document), not started.
- Phases 8–9 (Order Employee, Sales Employee): unchanged, future work,
  per the renumbering in `66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.

## Numbering note — resolved
`23_AS_BUILT_CURRENT_STATE_v0.6.0.md` flagged that the Roadmap's original
"فاز ششم" (Invoice Employee) and this project's "Phase 6" (Stripe
adapter) both used the same number. This is now resolved:
`64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md` keeps its existing
"Phase 6" name (as-built documents for shipped releases aren't renamed
after the fact); the Roadmap's Employee sequence is renumbered forward by
one, so Invoice Employee is **Phase 7**, Order Employee is **Phase 8**,
and Sales Employee is **Phase 9**. Full detail in
`66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.
