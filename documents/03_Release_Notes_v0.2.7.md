# Release Notes — AI Employee Platform v0.2.7

## Scope
Phase 1 — Core / RBAC and Tenant Isolation.

## Changed
- Fixed PostgreSQL-specific upsert behavior in tenant-admin RBAC provisioning.
- Updated backend application version from 0.2.6 to 0.2.7.
- Added explicit registration regression/testing documentation under `documents/`.

## Files changed
- `backend/app/services/auth_service.py`
- `backend/app/main.py`
- `backend/pyproject.toml`
- `backend/README.md`
- `backend/CHANGELOG.md`
- `CHANGELOG.md`
- `PROJECT_FILE_MANIFEST.json`

## No database migration
This is a code-level compatibility fix. Existing PostgreSQL schema and RBAC tables do not need a new migration for this change.

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

