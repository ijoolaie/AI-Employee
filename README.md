# AI Employee Platform — Release Candidate

**Version:** 1.0.0-rc.9

This repository contains the synchronized implementation and certification baseline for the AI Employee Platform. RC9 is built on the completed RC8 functional baseline and adds CI/certification hardening plus subsequent production-deployment hardening.

## Current release position

**Phase: RELEASE / final release preparation**

The repository-level certification and product-acceptance gates are complete. Production hardening, local production deployment, readiness, and rollback-drill evidence have also been completed on the current certified deployment-tested revision.

Current deployment-tested revision:

`27dc0aa5651b60afe171cada831185d28b73f58c`

Do not restart the roadmap from RC8 certification tasks. Those gates are completed evidence and remain valid unless a later code/configuration change affects the relevant behavior.

## Evidence already completed

- GitHub Actions Architecture Guard — PASS
- Production Compose Validation — PASS
- Production Certification — PASS
- Product Acceptance — PASS
- Production Hardening — PASS
- PostgreSQL backup/restore smoke — PASS
- Redis persistence/restore smoke — PASS
- Disaster Recovery — PASS
- Production Observability contract — PASS
- Failure detection / rollback contract — PASS
- Deployment Readiness — PASS
- Immutable release revision / manifest — PASS
- Local production Docker deployment — PASS
- Local production API/frontend/worker/beat/PostgreSQL/Redis readiness — PASS
- Local controlled API failure detection and recovery drill — PASS

## Remaining release work

The remaining work is release-integrity and release execution, not re-certification of completed product gates:

1. Keep version/release documentation synchronized with RC9 and the deployment-tested revision.
2. Create/verify the final GitHub release tag from the certified revision.
3. Publish the release evidence/artifacts and release notes.
4. If an actual external production target exists, configure the GitHub `production` environment and perform live deployment, external alert delivery, and live rollback evidence separately.

## Start here

1. Read `docs/current/00_MASTER_IMPLEMENTATION_GUIDE.md`
2. Read `docs/current/04_RELEASE_AUDIT.md`
3. Read `docs/current/05_CERTIFICATION_PROGRESS.md`
4. Read `docs/current/09_PRODUCTION_READINESS_STATUS.md`
5. Read `docs/current/RELEASE_POSITION_2026-08-20.md`
6. Use `docs/current/02_WINDOWS_RUNBOOK.md` for local production operations

## Migration note

The current Alembic graph must remain authoritative. Run `alembic upgrade head` and `alembic check`; do not stamp the database to conceal a mismatch.

## Release policy

A green certification gate is a completed checkpoint. Do not rerun or weaken already-passing gates merely because a later release step is pending. Release only from an immutable revision whose required evidence is recorded.
