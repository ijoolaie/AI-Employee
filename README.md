# AI Employee Platform

**Latest published release:** `v1.0.1`

This repository contains the AI Employee Platform implementation, certification evidence, release infrastructure, and productization roadmap.

## Current source/release position

- **Published release:** `v1.0.1` at commit `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- **Current `main`:** contains post-release CI/release-topology work and is not automatically the same as the published release.
- **Productization roadmap:** `docs/current/PRODUCTIZATION_ROADMAP.md`.
- **Release topology:** vendor → reseller → customer editions are explicitly separated and must not share higher-level control-plane access.

Certification and production-hardening evidence completed for the release line remains valid unless a later code/configuration change affects the relevant behavior. Do not restart completed RC8/RC9 certification work merely because productization or release-integrity work is pending.

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

## Productization sequence

1. Release Integrity
2. Vendor Edition
3. Reseller Edition
4. Customer Edition
5. Repeatable Delivery Package
6. Commercial Production

See `docs/current/PRODUCTIZATION_ROADMAP.md` for the detailed phase gates and definition of commercially deliverable.

## Start here

1. `docs/current/00_MASTER_IMPLEMENTATION_GUIDE.md`
2. `docs/current/04_RELEASE_AUDIT.md`
3. `docs/current/05_CERTIFICATION_PROGRESS.md`
4. `docs/current/09_PRODUCTION_READINESS_STATUS.md`
5. `docs/current/PRODUCTIZATION_ROADMAP.md`
6. `docs/current/02_WINDOWS_RUNBOOK.md`

## Migration note

The current Alembic graph must remain authoritative. Run `alembic upgrade head` and `alembic check`; do not stamp the database to conceal a mismatch.

## Release policy

A green certification gate is a completed checkpoint. Re-run only gates affected by later code/configuration changes. Every published release must point to an immutable commit and its documentation, manifest, evidence, and artifacts must match that exact release.
