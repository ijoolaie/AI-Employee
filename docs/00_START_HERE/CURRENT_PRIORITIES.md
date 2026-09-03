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

## Priority 2 — Phase 12 P12.4: Evidence & Artifacts

The P12.1-P12.3 backend contract is now verified by green CI run `33629549153`.

Next, implement durable evidence/artifact handling for Test Runs:

- structured pass/fail results;
- logs and artifact references;
- runtime/version identity;
- migration identity;
- relevant SHA/checksum identity;
- explicit engineering/local/external evidence boundaries.

## Priority 3 — Phase 12 P12.5: Run History

Add tenant/workspace-scoped run history with:

- role-aware visibility;
- filtering by test, status and date;
- immutable result history;
- preserved tenant isolation.

## Priority 4 — Phase 12 P12.6: Exportable Verification Records

Create an exportable verification record suitable for local delivery and future acceptance workflows without falsely claiming external acceptance.

## Priority 5 — Authorized Test Center UI

After the P12 backend contracts are extended and verified, add the Test Center UI incrementally through authorized Platform/Reseller/Client workspace boundaries.

## Priority 6 — Unified execution and workspace hardening

Continue validating Platform, Reseller and Client actions against real WorkItem and Agent APIs, preserving tenant, RBAC, approval and audit boundaries.

## Priority 7 — Compatibility migration

Continue moving changed Employee-backed capabilities toward the unified Human/Agent execution model without destructive model replacement.

## Priority 8 — Future conditional external production

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
