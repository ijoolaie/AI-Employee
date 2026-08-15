# Phase 4 — Monetization As-Built v0.4.2

## Scope implemented

This release moves the platform from the v0.4.1 technical baseline into the Monetization implementation gate defined by `03_Roadmap_v1.1`.

### Plans

Three tenant plans are now represented as first-class database records:

- Starter
- Business
- Professional

The repository contains technical default limits and prices so the billing system is executable and testable. These defaults are implementation values, not a claim that final commercial pricing has been approved.

### Subscription lifecycle

Each tenant receives a Starter subscription during registration. The API supports:

- list active plans;
- read current tenant subscription;
- change plan;
- cancel immediately or at period end.

Subscription state is provider-neutral and stores provider/customer/subscription identifiers for an eventual payment adapter.

### Entitlements / quotas

Quota checks are now enforced at service boundaries:

- monthly workflow/employee run count;
- monthly AI token consumption;
- active tenant employee count;
- active tenant workflow count.

The existing AI Provider Call records remain the usage source of truth.

### Billing events

An idempotent `billing_events` table accepts provider-normalized subscription events. The endpoint fails closed unless `BILLING_WEBHOOK_SECRET` is configured and supplied.

This keeps payment-provider details outside the core entitlement model and allows a Stripe/Adyen/etc. adapter to be added without changing quota logic.

### MRR evidence

Platform admins now have `/api/v1/admin/billing`, exposing active subscriptions, paid subscribers, MRR and plan distribution from durable subscription state.

## Phase 4 gate status

**Implementation gate: substantially implemented.**

**Commercial exit gate: not yet proven.** The roadmap requires positive and growing MRR plus a defined minimum number of paying subscribers. Those are production/business evidence, not values that can legitimately be fabricated by tests or seed data.

Before declaring Phase 4 complete:

1. configure a real payment provider adapter and webhook verification;
2. run real paid subscription transactions;
3. verify upgrade/downgrade/cancellation webhooks end-to-end;
4. collect the roadmap-required paid-subscriber and MRR evidence;
5. freeze the resulting release baseline.
