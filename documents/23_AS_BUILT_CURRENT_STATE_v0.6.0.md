# AS-BUILT CURRENT STATE — v0.6.0

## Governance note (read first)
Per `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, further roadmap phases
were recommended to wait until Phase 4's commercial exit gate was closed.
Phase 5 (Document Employee) was built ahead of that gate at explicit user
direction. When asked whether to proceed to Phase 6 (Invoice Employee) or
return to close the Phase 4 gate first, **the user chose to return and
close the gate**. This release (v0.6.0) is that work: a real Stripe
payment-provider adapter. See
`documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md` for the full
verification boundary — the commercial gate is still not fully proven
(no live Stripe transaction was possible from this delivery environment),
but the implementation gap is now closed.

## Phase 1 (cumulative, unchanged)
See `23_AS_BUILT_CURRENT_STATE_v0.2.47.md`.

## Phase 2 (cumulative) — CLOSED
Report Employee. See `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.

## Phase 3 (cumulative) — tooling shipped
Validation feedback/dashboard tooling. See
`59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md`.

## Phase 4 (cumulative) — implementation now substantially complete, commercial proof still pending
Billing plans/subscriptions/entitlements/MRR reporting (provider-neutral
core) plus, as of this release, a real Stripe adapter. See
`62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md`,
`61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, and
`64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`.

## Phase 5 (cumulative) — Document Employee, code-complete
See `63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`. Not exercised
against a live stack or real documents/users as of this document.

## Phase 6 additions (this release) — Stripe payment-provider adapter
- Added `app/services/stripe_service.py`: real Stripe Checkout Session
  creation, real Stripe Billing Portal session creation, Stripe webhook
  signature verification, and webhook-event-to-billing-state translation.
- Added `POST /api/v1/billing/checkout`, `POST /api/v1/billing/portal`,
  and the public `POST /api/v1/webhooks/billing/stripe` receiver.
- Added Stripe configuration to `app/core/config.py`, fail-closed when
  unset.
- Updated the customer Billing page to route paid-plan selection through
  real Stripe Checkout and added a "Manage billing" Stripe Portal link.
- Zero new Alembic migrations — the `Subscription` model already had
  provider/provider_customer_id/provider_subscription_id columns from
  Phase 4, built provider-neutral in anticipation of this.
- Full detail: `64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`.

## Verification boundary
- Python compile/static checks: PASS.
- Backend test suite: **121 passed** in this build environment (113
  carried over from v0.5.0 + 8 new in `tests/test_stripe_service.py`,
  including genuine offline HMAC-SHA256 webhook-signature verification
  and rejection tests — not mocks).
- Static Alembic head analysis: unchanged, exactly one head
  (`0a1b2c3d4e5f`).
- All three new API routes confirmed present in the live app's generated
  OpenAPI schema (62 total paths).
- **Real Stripe API calls (Checkout Session creation, Portal session
  creation, a real webhook delivery) were NOT and cannot be made from
  this delivery environment** — its network egress allowlist does not
  include any Stripe domain. This is the single most important
  unverified item in this release; see the Phase 6 As-Built document's
  "Required manual steps" section before treating the commercial gate as
  closed.

## Where the project stands against the Roadmap
- Phase 0 (Foundation): documented/agreed.
- Phase 1 (Core): CLOSED.
- Phase 2 (Report Employee): CLOSED (user-reported, 2026-08-09).
- Phase 3 (Validation): tooling shipped; phase itself not independently
  confirmed complete.
- Phase 4 (Monetization): implementation gate now includes a real payment
  adapter (this release); the **commercial** exit gate (proven real MRR +
  minimum paid subscribers) remains open pending a live Stripe run by the
  project owner.
- Phase 5 (Document Employee): code-level IMPLEMENTED; not yet exercised
  against a live stack.
- Phase 6 (real payment provider): code-level IMPLEMENTED and unit-tested
  to the limit this environment allows; live verification pending.
- Phases 7–8 (Order/Sales Employee, or as renumbered once Phase 6's
  original Roadmap slot is reconciled — see note below): unchanged,
  future work.

## A numbering note
The Roadmap's original §9 labeled "فاز ششم" as the next specialized
Employee (Invoice Employee) in the Report/Document Employee sequence.
This release used the "Phase 6" label instead for closing the Phase 4
commercial gate, per the user's explicit choice when asked to pick
between continuing the Employee sequence or returning to Phase 4. A
future roadmap synchronization pass should reconcile this numbering
(e.g., treating this as "Phase 4b" or renumbering subsequent Employee
phases) rather than silently having two different things both called
"Phase 6" — flagged here so it isn't missed.
