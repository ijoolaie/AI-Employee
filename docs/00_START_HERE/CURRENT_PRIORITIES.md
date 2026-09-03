# Current Priorities

**Reconciled:** 2026-09-03

## Priority 0 — Preserve verified identities and evidence

Preserve:

- canonical `v1.3.2` identity at `728b7f447d3bc6376fb01d47730cdd70eaf07746`;
- completed local Product Acceptance evidence;
- local runtime hardening and DR/restore evidence;
- the verified Alembic graph and migration lineage.

Do not rerun completed suites merely to reproduce status. Rerun only when regression risk or explicit evidence invalidation exists.

## Priority 1 — Customer Delivery Package

Prepare the customer delivery and handoff package for the current local-delivery scope. Do not claim customer deployment or acceptance before an actual customer event exists.

## Priority 2 — Phase 12: Test Center backend foundation

**IMPLEMENTED / VERIFIED.** P12.1-P12.3 provide tenant-bound definitions, safe execution, authorization boundaries, lifecycle transitions, cancellation and row-lock concurrency protection. Expiration is now both explicitly invokable and automatically swept by Celery Beat using the configured `TEST_CENTER_RUN_TIMEOUT_SECONDS` policy.

## Priority 3 — Phase 12 P12.4: Evidence & Artifacts

**IMPLEMENTED / VERIFIED.** Test Runs persist structured results, evidence, runtime/version identity, migration identity, git SHA/checksum identity and an explicit engineering/product evidence boundary. Completed runs can carry tenant-scoped artifact references with SHA-256 and metadata.

## Priority 4 — Phase 12 P12.5: Run History

**IMPLEMENTED / VERIFIED.** Read-only history is tenant/workspace scoped with test, status and date filtering, bounded pagination and stable newest-first ordering. The active-run expiry sweep uses a dedicated status/time index and preserves row-lock transition safety.

## Priority 5 — Phase 12 P12.6: Exportable Verification Records

**IMPLEMENTED / VERIFIED.** Completed Test Runs can produce an immutable tenant-scoped verification snapshot containing run identity, definition, result/evidence identity and artifact references. The record explicitly states that it is engineering/product evidence and does not constitute Vendor, Reseller, Customer or external production acceptance.

## Priority 6 — Authorized Test Center UI

**IMPLEMENTED / VERIFIED.** The customer-facing Test Center UI is merged to `main` and consumes the authorized backend contract for definitions, runs, history, artifacts and verification export.

## Priority 7 — Unified execution and workspace hardening

Continue validating Platform, Reseller and Client actions against real WorkItem and Agent APIs, preserving tenant, RBAC, approval and audit boundaries.

## Priority 8 — Compatibility migration

Continue moving changed Employee-backed capabilities toward the unified Human/Agent execution model without destructive model replacement.

## Priority 9 — Future conditional external production

Only when a real external target exists:

- configure the real deployment context;
- collect deployment/observability/recovery evidence;
- execute Vendor → Reseller → Client acceptance where applicable.

Never fabricate production configuration merely to satisfy CI.

## Downstream roadmap

After Phase 12 is operationally stable:

1. Phase 13 — Agent Teams & Marketplace.
2. Phase 14 — Scale, Governance & Production.

## Evidence boundary

- CI/internal certification = engineering evidence.
- Local real-stack validation = local evidence.
- External production and customer acceptance require independent external evidence.
- Phase 12 verification does not change canonical v1.3.2 certification identity.
