# AI Employee Platform — Clean Release Candidate

**Version:** 1.0.0-rc.8

This repository is a cleaned, synchronized implementation baseline containing:

- `backend/` — FastAPI + PostgreSQL + Redis + Celery
- `frontend/` — Next.js + React + TypeScript
- `documents/` — historical and source design documents
- `docs/current/` — authoritative current implementation/runbook/user guide
- `scripts/` — Windows bootstrap and verification helpers

## Start here

1. Read `docs/current/00_MASTER_IMPLEMENTATION_GUIDE.md`
2. Read `docs/current/01_ARCHITECTURE_AND_MODULE_MAP.md`
3. Run `scripts/bootstrap.ps1`
4. Follow `docs/current/02_WINDOWS_RUNBOOK.md`
5. Use `docs/current/03_USER_GUIDE.md`
6. Use `docs/current/04_RELEASE_AUDIT.md` when verifying the release

## Important migration note

The RC8 archive contains the complete migration graph. The current Alembic head is:

`rc8p0p4pwd`

Do not stamp the database to conceal a mismatch. Run `alembic upgrade head` and then `alembic check`.

## Release status

This is a **release candidate for structured local implementation/testing**. It is not a claim of production certification until the runtime test gates pass.


## RC8 User Execution Kit

For the shortest run path for each supported user persona, see `docs/runbooks/USER_EXECUTION_KIT.md`. PowerShell persona scripts are under `scripts/personas/`.
