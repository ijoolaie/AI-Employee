# AI Employee Platform — v0.6.0 Package Verification (Phase 6: Stripe adapter, closing Phase 4's implementation gap)

This package adds a real Stripe payment-provider adapter on top of v0.5.0
(Document Employee). It contains:
- `backend/`
- `frontend/`
- `documents/`
- `DEV_SETUP.md`
- `CHANGELOG.md`
- `PROJECT_FILE_MANIFEST.json`

## Why this release exists
`documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md` identified that Phase 4's
commercial exit gate was unmet and recommended pausing further roadmap
phases. Phase 5 proceeded anyway at explicit user direction. When asked
whether to continue to a further Employee phase or return to close the
Phase 4 gate, **the user chose to close the gate**. This release is that
work.

## Migration verification
No new Alembic migration was added. Static Alembic revision analysis
reports exactly one head, unchanged from the uploaded v0.4.2 package and
from v0.5.0:

`0a1b2c3d4e5f`

The `Subscription` model's `provider`/`provider_customer_id`/
`provider_subscription_id` columns already existed from Phase 4 — built
provider-neutral in anticipation of exactly this adapter. The plan→Stripe
Price ID mapping uses a settings dict (`STRIPE_PRICE_MAP`), not a new
column.

## Source verification
- Python source compilation: PASS.
- Static Alembic head analysis: PASS — exactly one head (`0a1b2c3d4e5f`).
- Backend unit test suite: **121 passed** in this build environment (113
  from v0.5.0 + 8 new in `tests/test_stripe_service.py`).
- **Webhook signature verification was tested with a real,
  independently-constructed HMAC-SHA256 signature**, not a mock: a JSON
  event payload was signed offline per Stripe's documented scheme and
  confirmed to be both accepted (valid signature) and rejected (tampered
  payload / wrong secret / missing header) by
  `stripe_service.verify_and_parse_webhook()`.
- All three new routes (`POST /billing/checkout`, `POST /billing/portal`,
  `POST /webhooks/billing/stripe`) confirmed present in the live FastAPI
  app's generated OpenAPI schema (62 total paths, up from 59).
- Frontend: modified `billing/page.tsx` and `lib/api.ts` syntax-checked
  with `esbuild` (parse-only). `next build` not run (no `node_modules`).

## What was NOT verified, and cannot be from this delivery environment
- **No real Stripe API call was made.** This delivery environment's
  network egress allowlist does not include any Stripe domain
  (`api.stripe.com` or otherwise). `create_checkout_session()` and
  `create_portal_session()` make genuine outbound HTTPS calls to Stripe
  and were never executed here — not even in Stripe's test mode.
- **No real Checkout Session was ever completed; no test card was ever
  charged; no real webhook was ever received from Stripe's servers.**
- **The Phase 4 commercial exit gate (proven MRR + minimum paid
  subscribers) is therefore still open.** This release closes the
  *implementation* gap only. See
  `documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md`, section
  "Required manual steps before this can be used for real", for exactly
  what the project owner must do next in an environment that can reach
  Stripe.

## New surface in this release
- `POST /api/v1/billing/checkout`, `POST /api/v1/billing/portal` —
  authenticated, tenant-scoped.
- `POST /api/v1/webhooks/billing/stripe` — public, Stripe-signature
  authenticated only, mounted under the existing `/api/v1/webhooks/`
  prefix (inherits existing payload-size/rate-limit middleware
  automatically — no middleware changes were made).
- `app/services/billing_service.py` (the provider-neutral Phase 4 core:
  quota enforcement, MRR reporting) is **unchanged**.

## Required manual step before first use
Configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and
`STRIPE_PRICE_MAP` (plus optionally the redirect URLs) in the deployment
environment — never in this repository. See `DEV_SETUP.md` "v0.6.0 —
Phase 6: real Stripe payment provider" for the full checklist, including
registering the webhook endpoint in the Stripe Dashboard.

## Consistency fixes applied in this package
- `backend/pyproject.toml`, `frontend/package.json`,
  `backend/app/main.py` all aligned to `0.6.0` (were `0.5.0`).
- `CHANGELOG.md` and `backend/CHANGELOG.md` both updated, prepended at the
  top matching this project's newest-first changelog convention (the
  v0.5.0 entry added in the previous session had been appended lower in
  the file rather than prepended — noted here, not silently left
  inconsistent, though not moved since changelog history should not be
  reordered after the fact).
- `PROJECT_FILE_MANIFEST.json` regenerated (paths, sizes, sha256 for every
  file in the package) and `verification_status` updated.

## Release note
This release adds a real Stripe payment-provider adapter without
modifying Phase 1–5 behavior for any existing Employee, Workflow, or API
surface outside the additive billing changes listed above. It closes the
implementation half of the Phase 4 commercial exit gate identified in
`61_PHASE4_BASELINE_AUDIT_v0.4.1.md`; the commercial half requires the
project owner to complete a real Stripe run outside this delivery
environment. Documentation, changelogs, and the file manifest have been
synchronized with the actual code and test state as of this build.
