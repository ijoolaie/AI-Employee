# Release Position — 2026-08-20

## Current state

**Published release: `v1.0.1`**

The repository has completed the major implementation, certification, product-acceptance, production-hardening, deployment-readiness, and release-evidence gates for the current release line. The next work is release integrity and commercial productization, not restarting earlier certification phases.

## Published release baseline

- Published version: `v1.0.1`
- Published release commit: `2d23a01098f432145ecaea14b2500fe520ad0bf7`
- `main` contains post-release CI/release-topology work and must be intentionally versioned before those changes are claimed as part of a release.

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

## Productization sequence

1. **Release Integrity** — synchronize published release, current `main`, and certified delivery baselines.
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
