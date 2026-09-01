# Current Priorities

## Priority 0 — Preserve v1.3.2 Release Identity

The canonical candidate is `v1.3.2` on `release/v1.3.2-phase6e-candidate` at exact commit `728b7f447d3bc6376fb01d47730cdd70eaf07746`. Phase 6E rehearsal, Production Certification and release packaging have passed on that exact identity. Do not rebuild, retag or replace it without a real defect.

## Priority 1 — Production Target Prerequisite

A real production target is required before target-specific evidence can be collected. The deployment workflow requires `PRODUCTION_DEPLOY_HOST`, `PRODUCTION_DEPLOY_USER`, `PRODUCTION_DEPLOY_SSH_KEY` and `PRODUCTION_CONTAINER_REGISTRY`, and verifies deployment against an immutable revision. Until a target exists and is configured, target deployment and target-specific production evidence remain blocked.

## Priority 2 — Target-Specific Production Hardening

Once the target exists, execute the repository's production hardening and observability workflows against the exact candidate revision. Do not classify workflow existence as production evidence.

## Priority 3 — Recovery, DR and Rollback

Run target-specific backup/restore, disaster-recovery and controlled rollback exercises on the exact release identity. Preserve logs, artifacts and recovery evidence for the final reconciliation.

## Priority 4 — Exact-Revision Deployment & Smoke Verification

Deploy `v1.3.2` / `728b7f447...` to the real target, verify health/readiness and product behavior, and reconcile deployment revision with migration and artifact identities.

## Priority 5 — Final Evidence Reconciliation

Build one authoritative evidence manifest tying together version/tag, exact SHA, migration head, certification runs, runtime checksum, edition checksum, deployment revision, observability, recovery/DR and rollback evidence.

## Priority 6 — External Acceptance

Only after the target-specific gates pass may the project enter the external Vendor → Reseller → Client acceptance sequence. There is currently no Vendor acceptance event to record.

## Priority 7 — Phase 12 Test Center & Evidence Platform

Expand existing test/evidence contracts into the first-class Phase 12 Test Center where repeatable acceptance proof is needed, without destabilizing the release candidate.

## Priority 8 — Compatibility Migration

Continue incremental migration of existing Employee-backed capabilities onto the unified Human/Agent execution model while preserving compatibility paths.

## Priority 9 — Downstream Productization

After productionization and execution stability, proceed with Phase 13 Agent Teams & Marketplace and Phase 14 Scale, Governance & Production.

## Evidence boundary

- CI/internal certification is engineering evidence.
- A GitHub release/tag is a release identity, not proof of production deployment.
- External Vendor/Reseller/Client acceptance requires independent evidence.
- No acceptance state may be marked complete without the corresponding external evidence.
