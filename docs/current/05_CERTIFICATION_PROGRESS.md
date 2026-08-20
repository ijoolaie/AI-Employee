# Certification Roadmap Progress

## Status as of 2026-08-20

**Current state: RELEASE / final release preparation.**

The repository-level certification, product acceptance, production hardening, deployment readiness, release evidence, and local production recovery gates are complete. The roadmap must not loop back to already-passed RC8/RC9 certification work.

## Completed certification stack — DO NOT REOPEN WITHOUT AFFECTING CHANGE

The certified GitHub Actions stack has already passed:

1. Python/npm dependency setup with CI caches
2. Playwright Chromium installation
3. Python compilation and Ruff
4. Compose-managed PostgreSQL and Redis readiness
5. Alembic migration
6. Backend tests
7. Frontend contract tests, unit tests and production build
8. Production-like Docker stack startup/readiness
9. OCR runtime and Farsi language verification
10. OCR extraction
11. Backend dependency E2E
12. Auth P0
13. Tenant isolation + RBAC P0
14. Employee -> Run -> AI -> Result
15. Files -> Knowledge -> Memory
16. Admin / Developer API Keys
17. Workflow -> Approval -> Schedule
18. Orders -> Sales -> Invoice -> Billing
19. Frontend Playwright E2E
20. Stack cleanup

**These gates are completed evidence.** They should only be rerun when a later code/configuration change affects the relevant area.

## Completed production-hardening gates

- Production configuration guards
- Production Compose validation
- Production certification
- Product acceptance
- Backup/restore smoke checks
- Disaster recovery
- Observability contract
- Failure detection and rollback contract
- Notification delivery contract
- Deployment readiness
- Immutable release revision / manifest

## Completed local production evidence

Certified deployment-tested revision:

`27dc0aa5651b60afe171cada831185d28b73f58c`

Local Docker production-like stack evidence:

- API healthy and `/health/dependencies` → `LOCAL_PRODUCTION|readiness|PASS`
- Frontend healthy
- PostgreSQL healthy
- Redis healthy
- Worker healthy
- Beat running
- Controlled API stop detected as failure
- API recovery verified → `ROLLBACK_DRILL|recovery|PASS`
- Working tree clean after the drill

## Current roadmap — RELEASE

### Release integrity

- [x] Align release documentation with RC9 and current deployment-tested revision.
- [x] Record current release position and completed evidence.
- [ ] Create/verify the final GitHub release tag from the certified revision.
- [ ] Publish release notes and accumulated release evidence/artifacts.

### Optional live-production certification

These are **environment-specific**, not blockers for repository release preparation unless a real production target is required:

- [ ] Configure the GitHub `production` environment and real deployment secrets.
- [ ] Execute a live deployment to the real production target.
- [ ] Verify external alert-provider delivery.
- [ ] Execute a live rollback to the previous immutable revision.

## Operating rule

**A green certification gate is the checkpoint; a failed later gate is the next task. Do not modify already-passing behavior merely to make a later gate pass. Do not rebuild dependencies or repeat setup on every workflow run when the workflow can reuse CI caches and immutable build artifacts.**
