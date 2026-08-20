# Release Position — 2026-08-20

## Current state

**RELEASE / final release preparation**

The repository has completed the major implementation, certification, product-acceptance, production-hardening, deployment-readiness, and release-evidence gates. The current task is release-integrity and release execution, not restarting earlier certification phases.

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
- Local production Docker deployment: PASS.
- Local production API, frontend, worker, beat, PostgreSQL, and Redis readiness: PASS.
- Controlled local API failure detection and recovery drill: PASS.

## Certified deployment-tested revision

`27dc0aa5651b60afe171cada831185d28b73f58c2`

## Do not reopen completed gates

Earlier RC8/RC9 certification work is retained as evidence. A later release step does not require rebuilding dependencies, reinstalling toolchains, or rerunning unrelated certification gates unless the relevant code/configuration changed.

## Remaining release sequence

1. Keep version/release documentation aligned with RC9 and the deployment-tested revision.
2. Create/verify the final release tag from the certified revision.
3. Publish the release evidence/artifacts and release notes.
4. If an external production target is available, perform the separate live-production deployment, alert-delivery, and live-rollback evidence.

## Important distinction

Local production deployment and rollback evidence prove the repository's deployment/recovery behavior on the local Docker production-like stack. They do not fabricate evidence for an external production host, registry, alert provider, or live customer environment.
