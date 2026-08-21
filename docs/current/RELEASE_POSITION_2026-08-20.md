# Release Position — 2026-08-20

## Current state

**Current release target: `v1.1.1`**

The repository has completed the major implementation, certification, product-acceptance, production-hardening, deployment-readiness, and release-evidence gates for the prior release line. The current `v1.1.1` line records delivery, migration, CI, and documentation hardening after the immutable `v1.1.0` vendor release.

## Release baseline

- Current release target: `v1.1.1`
- Base immutable vendor release: `v1.1.0`
- Historical rollback reference: `v1.0.1`
- Current `main` is the vendor source-of-truth revision for the v1.1.1 validation line.

## Certified checkpoints

- RC8 functional baseline completed.
- RC9 CI/certification hardening completed.
- Architecture Guard: PASS.
- Production Compose Validation: PASS.
- Production Certification: PASS.
- Product Acceptance: PASS.
- Production Hardening: PASS.
- Backup/restore and disaster-recovery smoke checks: PASS.
- Observability, failure-detection, rollback, and notification contracts: PASS.
- Deployment Readiness and immutable release revision/manifest: PASS.
- Local production Docker deployment and readiness: PASS.
- Controlled local API failure detection and recovery drill: PASS.
- Alembic migration-head merge: completed in the v1.1.1 hardening line.
- Backend and frontend package versions: aligned to `1.1.1`.

## v1.1.1 release hardening

The v1.1.1 line includes:

1. Release-integrity alignment between `main` and the delivery-hardening baseline.
2. Backend package version alignment to `1.1.1`.
3. Frontend package version alignment to `1.1.1`.
4. Alembic migration-head merge so the migration graph has a single upgrade target.
5. Delivery manifest and packaging identity hardening.
6. Production deployment workflow environment scoping correction.
7. Documentation alignment with the v1.1 delivery architecture.

## Productization sequence

1. **Release Integrity** — synchronize current `main`, release metadata, and certified delivery baselines.
2. **Vendor Edition** — primary seller control plane, licensing, entitlements, global administration, and release authority.
3. **Reseller Edition** — delegated administration and customer provisioning inside a bounded reseller scope.
4. **Customer Edition** — isolated customer operations, configuration, data, recovery, and upgrade surface.
5. **Delivery Package** — reproducible artifact, manifest, installation, migration, backup/restore, rollback, and acceptance procedures.
6. **Commercial Production** — supported versions, update policy, support/escalation, and production evidence.

See `docs/current/PRODUCTIZATION_ROADMAP.md` for detailed gates and exit criteria.

## Do not reopen completed gates

Earlier RC8/RC9 certification work is retained as evidence. A later release/productization step requires new validation only where the relevant code or configuration changed.

## Important distinction

Local production deployment and rollback evidence proves deployment/recovery behavior on the local Docker production-like stack. It does not fabricate evidence for an external production host, registry, alert provider, or live customer environment.

## Production deployment gate

**Status: DEFERRED**

Live production deployment is not claimed complete until the production target secrets and environment are provisioned and the target deployment workflow is executed successfully.
