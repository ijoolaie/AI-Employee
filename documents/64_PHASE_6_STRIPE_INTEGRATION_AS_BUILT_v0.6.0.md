# PHASE 6 — REAL PAYMENT PROVIDER (STRIPE) — AS-BUILT — v0.6.0

## Status of this document
As-Built (describes what was actually implemented), not a plan. Follows
the verification rule from `documents/45_PHASE_1_SCOPE_LOCK_v0.2.34.md`.

## Why this release exists
`documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md` recorded that Phase 4's
commercial exit gate — real payment-provider integration and real MRR/
paid-subscriber evidence — was not met, and recommended holding further
roadmap phases until it was. After Phase 5 (Document Employee) was built
ahead of that gate at the user's direction (see
`documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`), the user
chose, when asked, to pause new-Employee work and close this gate first.
This release is that work: a real Stripe adapter on top of the existing
provider-neutral billing core from Phase 4.

## Scope
`app/services/billing_service.py` (Phase 4) was deliberately
provider-neutral: quota enforcement, MRR reporting, and the
`Subscription`/`BillingPlan`/`BillingEvent` models know nothing about any
specific payment provider. This release adds the Stripe-specific adapter
that plugs into that model — it does **not** modify
`billing_service.py`'s core logic, quota enforcement, or the MRR
calculation.

## What was implemented

### 1. `app/services/stripe_service.py`
- `create_checkout_session()` — creates a real Stripe Checkout Session
  (subscription mode) for a paid plan, mapping `BillingPlan.code` to a
  Stripe Price ID via `settings.stripe_price_map`. Creates (and caches on
  the tenant's `Subscription.provider_customer_id`) a Stripe Customer on
  first use. Returns the Checkout URL — card data never reaches this
  backend; Stripe hosts the actual payment form.
- `create_portal_session()` — creates a real Stripe Billing Portal
  session so a tenant can self-serve upgrade/downgrade/cancel/update
  payment method. This is what makes the Roadmap's "clear upgrade path"
  requirement (§9) real rather than an internal API call only an admin
  could trigger.
- `verify_and_parse_webhook()` — verifies the `Stripe-Signature` header
  against `STRIPE_WEBHOOK_SECRET` using the Stripe SDK's own HMAC-SHA256 +
  timestamp-tolerance scheme, and returns the parsed Event. Raises
  `ValidationAppError` on any failure (missing header, wrong secret,
  tampered payload) — this is the only path by which an unauthenticated
  caller can influence billing state, so it fails closed.
- `apply_webhook_event()` — translates a verified Stripe Event into calls
  to the existing, unmodified `billing_service.record_event()` /
  `Subscription` updates. Handles `checkout.session.completed`,
  `customer.subscription.created`/`updated`/`deleted`, and
  `invoice.payment_failed`. Idempotent by construction: `record_event()`
  already de-duplicates on `(provider, provider_event_id)`, so Stripe's
  at-least-once webhook delivery is safe to replay.
- Fails closed throughout: every function raises
  `StripeNotConfiguredError` (a `ValidationAppError` subclass) if
  `settings.stripe_enabled` is false (requires both a secret key and a
  webhook secret to be set) — an unconfigured deployment cannot
  accidentally look like it has working payments.

### 2. Configuration (`app/core/config.py`)
Added `stripe_secret_key`, `stripe_publishable_key`, `stripe_webhook_secret`,
`stripe_price_map` (a `dict[str, str]` of `plan_code -> Stripe Price ID`,
parsed from a JSON env var — no database schema change was needed for
this mapping), `stripe_checkout_success_url`, `stripe_checkout_cancel_url`,
`stripe_portal_return_url`, and a `stripe_enabled` property. All optional
and unset by default.

### 3. API surface
- `POST /api/v1/billing/checkout` (`app/api/v1/billing.py`) —
  authenticated, tenant-scoped; returns `{checkout_url}`.
- `POST /api/v1/billing/portal` — authenticated, tenant-scoped; returns
  `{portal_url}`.
- `POST /api/v1/webhooks/billing/stripe` (`app/api/v1/billing_webhooks.py`,
  a new router, since this endpoint is necessarily unauthenticated by
  user credentials — Stripe cannot supply a Bearer token). Deliberately
  mounted under the existing `/api/v1/webhooks/` prefix so it inherits
  the payload-size limit and rate limiting `app/core/middleware.py`
  already applies to that path family — no middleware changes were
  needed.
- Verified via `app.openapi()` that all three routes register correctly
  alongside the other 59 existing paths (62 total) — not just "the file
  compiles", but that FastAPI actually wires the routes.

### 4. Frontend (`app/(customer)/billing/page.tsx`)
- Choosing a paid plan now calls `POST /billing/checkout` and redirects
  the browser to the returned Stripe-hosted URL, instead of silently
  calling the internal `change_plan` endpoint (which remains available
  and is still used for the free `starter` plan, where no payment is
  needed).
- A "Manage billing (Stripe)" button appears once `subscription.provider
  === "stripe"`, calling `POST /billing/portal` and redirecting to
  Stripe's Billing Portal.

### 5. Dependency
`stripe>=11.0.0` (official Python SDK) added to `requirements.txt` and
`pyproject.toml`.

## What this release does NOT do
- **It does not modify `billing_service.py`'s quota enforcement or MRR
  calculation.** `admin_service`/`billing_service.platform_mrr()` reads
  the same `Subscription`/`BillingPlan` tables Stripe webhooks now update
  — no separate Stripe-specific reporting path was built, by design.
- **No Alembic migration.** The `Subscription` model already had
  `provider`, `provider_customer_id`, `provider_subscription_id` columns
  from Phase 4 (built provider-neutral in anticipation of exactly this).
  The plan→price mapping uses a settings dict, not a new table/column.
- **No handling of proration, trials, coupons, or tax** — the Roadmap's
  Phase 4/6 scope is "a working payment path", not a full revenue
  operations system. These are explicitly DEFERRED.
- **No admin UI for editing `STRIPE_PRICE_MAP`** — it is environment
  configuration (like `SMTP_HOST` or `DATABASE_URL`), not a
  database-editable setting, consistent with how other Phase 1–5
  provider credentials are handled in this codebase.

## The verification boundary — read this carefully
This is the most important section of this document, given why this
release exists.

**What was genuinely, mechanically verified in this build environment:**
- Python source compilation: PASS.
- Backend unit test suite: **121 passed** (113 carried over from v0.5.0 +
  8 new in `tests/test_stripe_service.py`).
- **Webhook signature verification was exercised with a real,
  independently-constructed HMAC-SHA256 signature** — not a mock, not an
  assertion about what the SDK "should" do. A JSON payload was signed
  offline using the documented Stripe scheme (`t={ts},v1={hmac}` over
  `f"{ts}.{payload}"`), and `stripe_service.verify_and_parse_webhook()`
  correctly accepted the valid signature and rejected a tampered payload,
  a wrong secret, and a missing header. This required no network access,
  because Stripe's webhook signature scheme is a local HMAC check.
- `settings.stripe_enabled` fail-closed behavior (no keys → all
  Stripe-dependent functions raise) was exercised directly.
- Plan-code-to-Stripe-Price-ID mapping logic was exercised directly.
- All three new routes (`/billing/checkout`, `/billing/portal`,
  `/webhooks/billing/stripe`) were confirmed present in the live FastAPI
  app's generated OpenAPI schema, alongside the 59 pre-existing paths.

**What was explicitly NOT verified, and cannot be from this delivery
environment:**
- **`create_checkout_session()` and `create_portal_session()` were never
  called against the real Stripe API.** This delivery environment's
  network egress allowlist does not include `api.stripe.com` (or any
  Stripe domain) — see the sandbox's network configuration. These two
  functions make genuine outbound HTTPS calls to Stripe and cannot be
  exercised here at all, not even in Stripe's test mode.
- **No real Checkout Session was ever completed.** No test-mode card was
  ever charged. No real `checkout.session.completed` webhook was ever
  received from Stripe's servers (only a locally-constructed one).
- **Therefore: the Phase 4 commercial exit gate (real MRR + minimum paid
  subscribers) is still NOT proven by this release alone.** This release
  closes the *implementation* gap identified in
  `61_PHASE4_BASELINE_AUDIT_v0.4.1.md` — a real payment-provider adapter
  now exists and is unit-tested — but proving the *commercial* gate
  requires the project owner to: configure real (or Stripe test-mode)
  API keys in an environment that can actually reach Stripe, complete at
  least one real Checkout flow, confirm the webhook lands and updates
  `Subscription` correctly end-to-end, and only then treat
  `GET /api/v1/admin/billing` (MRR/paid-subscriber counts) as meaningful
  evidence.

## Required manual steps before this can be used for real
1. Create a Stripe account (or use an existing one) and, for initial
   validation, use **test mode** keys first.
2. Create Stripe Products/Prices matching the `business` and
   `professional` `BillingPlan` rows (the free `starter` plan does not
   need a Stripe Price).
3. Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and
   `STRIPE_PRICE_MAP` (e.g.
   `STRIPE_PRICE_MAP='{"business":"price_...","professional":"price_..."}'`)
   in the deployment environment — **not** in this repository.
4. Register a webhook endpoint in the Stripe Dashboard pointing at
   `https://<your-domain>/api/v1/webhooks/billing/stripe`, subscribed to
   at minimum: `checkout.session.completed`,
   `customer.subscription.updated`, `customer.subscription.deleted`,
   `invoice.payment_failed`.
5. Complete one real (test-mode) Checkout flow end-to-end and confirm
   `GET /api/v1/billing/subscription` reflects the new plan/status, and
   `GET /api/v1/admin/billing` reflects it in `paid_subscribers`/`mrr_usd`.
6. Only after step 5 succeeds against a live Stripe test-mode account
   (and ideally after real customers have gone through it in live mode)
   should the Phase 4 commercial exit gate be considered closed.

## Package/version bump
- `backend/pyproject.toml`: `0.5.0` → `0.6.0`.
- `frontend/package.json`: `0.5.0` → `0.6.0`.
- `app/main.py` FastAPI `version=` bumped to `0.6.0`.
- No Alembic migration added; head remains `0a1b2c3d4e5f`.
