# AI Employee Platform — Release Candidate / Final Handoff

**Version:** 1.0.0-rc.8

This repository is a synchronized implementation and release baseline containing:

- `backend/` — FastAPI + PostgreSQL + Redis + Celery
- `frontend/` — Next.js + React + TypeScript
- `documents/` — historical and source design documents
- `docs/current/` — authoritative current implementation, release and handoff documentation
- `scripts/` — Windows bootstrap and verification helpers

## Current status

**Phase: RELEASE → FINAL HANDOFF**

The implementation roadmap, CI certification, release evidence/artifacts, and final production certification are already complete. Current work is limited to final release bookkeeping, handoff/sign-off, and post-release monitoring.

See `docs/current/ROADMAP.md` first for the authoritative roadmap.

## Start here

1. Read `docs/current/ROADMAP.md`
2. Read `docs/current/00_MASTER_IMPLEMENTATION_GUIDE.md`
3. Read `docs/current/04_RELEASE_AUDIT.md`
4. Read `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` for evidence
5. Use `docs/current/02_WINDOWS_RUNBOOK.md` for local operational commands
6. Use `docs/current/03_USER_GUIDE.md` for product usage

## Current verification snapshot — 2026-08-20

The local production stack was verified successfully:

- Compose configuration: PASS
- Production images: PASS
- API: healthy
- Frontend: healthy
- PostgreSQL: healthy
- Redis: healthy
- Celery worker: healthy
- Celery beat: running
- API readiness: PASS
- Controlled failure detection: PASS
- Recovery: PASS
- Working tree: clean at verification point

The rollback shell wrapper could not run through the available WSL distro because Docker Desktop integration was unavailable there. The equivalent drill was executed directly in PowerShell against Docker Desktop and passed.

## Important migration note

The RC8 archive contains the complete migration graph. The current Alembic head is:

`rc8p0p4pwd`

Do not stamp the database to conceal a mismatch. Run `alembic upgrade head` and then `alembic check` when establishing or upgrading an environment.

## Workflow execution rule

Dependencies and requirements are **not** rebuilt for every workflow run. Install/provision/build work is one-time or change-triggered. Once the environment is prepared, workflow runs should reuse the existing services and execute only the requested application work and acceptance checks.

## Release note

Older documents may describe this repository as staging-only or as awaiting certification. Those statements are historical and are superseded by `docs/current/ROADMAP.md` and `docs/current/04_RELEASE_AUDIT.md`.
