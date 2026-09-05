# Data Retention & Lifecycle Enforcement

**Reconciled:** 2026-09-05

## Purpose

Define a deterministic, tenant-scoped retention boundary for operational data without placing secrets or customer payloads in source control.

## Engineering policy

- Default retention window: **365 days**.
- Allowed operational window: 1–3650 days when the caller explicitly supplies the value.
- Audit logs: hard-delete records older than the retention cutoff for the selected tenant.
- Usage events: hard-delete records older than the retention cutoff for the selected tenant.
- Employee memory: hard-delete only lifecycle-terminal rows (`expired`, `deleted`, `superseded`) older than the cutoff. Active memory is never removed solely because it is old.
- Files: mark stale active file metadata as `deleted` and record `deleted_at`; physical object deletion remains storage-provider lifecycle work and must be verified on the target storage backend.
- Every cleanup operation is tenant-scoped and idempotent by predicate.
- No retention job accepts secrets on the command line.

## Execution

`backend/app/services/retention_service.py` exposes `enforce_retention()` for one tenant. `backend/scripts/enforce_retention.py` enumerates non-deleted tenants and executes the same policy in one controlled database session.

The runner resolves the application's normal database configuration and uses the 365-day default. Target operators should schedule it according to their deployment scheduler and approved retention policy.

## Safety boundary

This implementation is repository-level engineering evidence. It does **not** claim production compliance until the operator verifies the policy against the actual database, object storage, backup retention, legal holds, customer contract terms, and target scheduler.

In particular, physical deletion/version expiry for object storage and backup lifecycle must be configured and verified in the external storage platform; source code cannot prove those provider-side controls.

## Verification checklist

- [x] Tenant-scoped retention service.
- [x] Bounded retention window validation.
- [x] Audit-log cleanup.
- [x] Usage-ledger cleanup.
- [x] Terminal-memory cleanup.
- [x] File metadata soft deletion.
- [x] Tenant-wide runner.
- [x] Unit coverage for policy bounds and tenant-scoped execution shape.
- [ ] Target scheduler configured and observed.
- [ ] Object-storage lifecycle/version expiration verified.
- [ ] Backup retention/legal-hold interaction reviewed.
- [ ] Production evidence attached to immutable release identity.
