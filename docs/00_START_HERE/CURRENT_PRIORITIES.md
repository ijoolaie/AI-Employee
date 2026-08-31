# Current Priorities

## Priority 0 — Preserve Phase 11 Closure

Phase 11 Unified Execution E2E acceptance is complete. Production Certification run 33369071987 on commit `bcacbc0eb03b247ad00a232e4eb6324ce5c849df` passed the Human and Agent real-stack gates with Failed gates: 0, and Issue #170 is closed. Reopen this scope only if new regression evidence appears.

## Priority 1 — Current-State / Release Reconciliation

Keep the roadmap and status documents aligned with the actual `main` branch, merged PRs, release tags and certification evidence. The current `main` is 221 commits ahead of the published `v1.3.0` tag, so `v1.3.0` must not be treated as the current implementation baseline. Do not create a release merely to make documentation current.

## Priority 2 — Production Hardening & External Evidence

Continue production hardening and independently collect environment-specific evidence. CI and internal Production Certification are engineering evidence, not proof of external production deployment, live provider behavior or customer acceptance.

## Priority 3 — Phase 5 / 6E External Delivery

When an intentional immutable release candidate is selected, execute the Vendor → Reseller → Client production delivery path with exact version/SHA, migration identity, artifact/checksum evidence and environment-specific acceptance. The implementation capability exists; the remaining claim is external evidence.

## Priority 4 — Workspace Operational Hardening

Continue Platform, Reseller and Client workspace verification under real role and tenant boundaries and address any regressions discovered after Phase 11. The canonical WorkItem/Agent API path is accepted for Phase 11; broader production behavior remains subject to external evidence.

## Priority 5 — Test Center & Evidence Expansion

Promote existing test/evidence contracts and service slices into the first-class Phase 12 Test Center once the execution substrate is operationally stable and productionization work is sufficiently controlled.

## Priority 6 — Compatibility Migration

Continue incremental migration of existing Employee-backed capabilities onto the unified Human/Agent execution model without breaking compatibility paths.

## Priority 7 — Downstream Productization

After productionization and execution stability, proceed with Phase 13 Agent Teams & Marketplace and Phase 14 Scale, Governance & Production.
