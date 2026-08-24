# Phase 5 — Commercial Production Foundation

Date: 2026-08-23

## Purpose

This document turns the remaining Phase 5 roadmap items into an executable production gate without reopening the certified core.

## Current implementation evidence

- Billing plans and subscriptions exist and subscription state is persisted per tenant.
- Quotas are enforced before AI run execution; employee and workflow quotas are enforced.
- Stripe subscription events are translated into provider-neutral billing state.
- Vendor → reseller → customer tenant boundaries and delegated customer entitlements are implemented.
- Commercial license authority, issuance/revocation, audit trail and fail-closed execution admission are implemented.
- Feature entitlements are enforced at the Tool Registry execution boundary for tenant-scoped business tools.
- Subscription lifecycle transitions cover expired trials, cancellation-at-period-end, cancellation, and active-period renewal.
- Release-channel and tenant upgrade admission policy is implemented for vendor, reseller and customer channels.
- Phase 4 delivery packaging/local validation is complete on the current branch.

## Local evidence — 2026-08-23

- Complete backend suite: **238 passed** locally.
- Production-like Docker readiness: API, PostgreSQL, Redis and frontend all exercised successfully using conflict-safe Windows validation ports.
- PostgreSQL logical restore + Redis AOF restore smoke: **PASS**.
- Controlled local recovery drill: failure detection and recovery: **PASS**.

See `docs/current/27_PHASE5_COMMERCIAL_PRODUCTION_EVIDENCE_2026-08-23.md` for the detailed evidence boundary.

## Phase 5 work packages

### P5.1 License authority

Status: **IMPLEMENTED / locally exercised**.

- immutable license identity
- issuer/owner identity
- tenant/edition binding
- issued_at / expires_at
- active/revoked status
- audit trail for issue and revoke
- fail-closed execution check

### P5.2 Commercial entitlement authority

Status: **IMPLEMENTED / locally exercised**.

- vendor can authorize reseller product/feature entitlements
- reseller can delegate only authorized entitlements to direct customers
- commercial license revocation blocks execution
- tenant feature entitlement enforcement blocks disabled capabilities
- quota limits cannot exceed the parent-authorized limit
- changes are auditable

### P5.3 Subscription lifecycle

Status: **IMPLEMENTED / locally tested**.

- active/trialing/past_due/canceled state transitions
- cancellation-at-period-end semantics
- provider webhook idempotency
- supported plan mapping
- expired-trial and unpaid-state behavior
- active subscription period renewal

### P5.4 Release channel policy

Status: **IMPLEMENTED / locally tested**.

- vendor/reseller/customer channel identifiers
- supported-version policy
- minimum supported version
- upgrade eligibility check
- downgrade rejection with rollback workflow separation
- tenant release upgrade persistence and audit

### P5.5 Production operations

Status: **LOCAL OPERATIONAL EVIDENCE COMPLETE FOR EXERCISED PATHS; EXTERNAL EVIDENCE REMAINS OPEN**.

- local production-like deployment/readiness evidence
- local backup/restore smoke evidence
- local recovery/rollback drill evidence
- production deployment evidence per real environment — pending
- external monitoring/alerting evidence — pending
- production-target rollback/recovery rehearsal — pending
- final security certification — pending
- commercial support/update-policy handoff — pending

## Acceptance rule

Do not mark Phase 5 complete from code presence alone. Each production target needs executable evidence for deployment, monitoring, recovery and security. Commercial controls must also be enforced at the execution boundary and remain fail-closed.

## Current completion boundary

Phase 5 implementation is substantially complete for the controls exercised on the branch. The remaining gates are evidence-dependent: GitHub Actions validation when capacity is available, real commercial revenue/subscriber proof, external deployment/monitoring/recovery evidence, final production security certification, and the final support/update-policy handoff.
