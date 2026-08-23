# Phase 5 — Commercial Production Foundation

Date: 2026-08-23

## Purpose

This document turns the remaining Phase 5 roadmap items into an executable production gate without reopening the certified core.

## Current implementation evidence

- Billing plans and subscriptions already exist.
- Subscription state is persisted per tenant.
- Quotas are enforced before AI run execution.
- Employee and workflow quotas are enforced.
- Stripe subscription events are translated into provider-neutral billing state.
- Vendor → reseller → customer tenant boundaries and delegated customer entitlements are implemented.
- Phase 4 delivery packaging/local validation is complete on the current working tree.

## Phase 5 work packages

### P5.1 License authority

Required:

- immutable license identity
- issuer/owner identity
- tenant/edition binding
- issued_at / expires_at
- active/revoked status
- audit trail for issue, renew, revoke
- fail-closed execution check

### P5.2 Commercial entitlement authority

Required:

- vendor can authorize reseller product/feature entitlements
- reseller can delegate only authorized entitlements to direct customers
- entitlement revocation propagates to execution boundaries
- quota limits cannot exceed the parent-authorized limit
- all changes are auditable

### P5.3 Subscription lifecycle

Required:

- active/trialing/past_due/canceled state transitions
- cancellation-at-period-end semantics
- provider webhook idempotency
- supported plan/version mapping
- explicit behavior for expired trials and unpaid subscriptions

### P5.4 Release channel policy

Required:

- vendor/reseller/customer channel identifiers
- supported-version policy
- minimum supported version
- upgrade eligibility check
- rollback target recording

### P5.5 Production operations

Required per real environment:

- deployment evidence
- external monitoring/alerting evidence
- backup/restore rehearsal
- rollback/recovery rehearsal
- final security certification
- support escalation ownership and response policy

## Acceptance rule

Do not mark Phase 5 complete from code presence alone. Each production target needs executable evidence for deployment, monitoring, recovery and security. Commercial controls must also be enforced at the execution boundary and remain fail-closed.

## Immediate implementation order

1. License/entitlement authority and revocation model.
2. Execution-boundary enforcement tests.
3. Supported-version/release-channel policy.
4. Production deployment + monitoring evidence.
5. Backup/restore and rollback rehearsals.
6. Final security certification and commercial handoff.
