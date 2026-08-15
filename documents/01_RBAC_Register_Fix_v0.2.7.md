# AI Employee Platform — RBAC Registration Fix v0.2.7

Date: 2026-08-07
Phase: Phase 1 — Core
Step: 01 — RBAC and Tenant Isolation

## Problem
`POST /api/v1/auth/register` returned HTTP 500 during tenant registration. The traceback ended with:

```text
AttributeError: 'Insert' object has no attribute 'on_conflict_do_nothing'
```

The failure occurred in `app/services/auth_service.py`, while creating the RBAC permission links.

## Root cause
The service imported `insert` from SQLAlchemy's generic namespace:

```python
from sqlalchemy import insert
```

The code then called PostgreSQL-specific `on_conflict_do_nothing()`. The generic `Insert` object does not expose that PostgreSQL method.

## Fix
The import is now:

```python
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
```

No RBAC data model or migration is required for this fix.

## Expected registration flow
1. Check tenant slug uniqueness.
2. Create tenant.
3. Create first user.
4. Resolve/create tenant `Admin` role.
5. Resolve/create Core permissions.
6. Create role-permission links with PostgreSQL `ON CONFLICT DO NOTHING`.
7. Create user-role link with PostgreSQL `ON CONFLICT DO NOTHING`.
8. Record audit events.
9. Commit the transaction through the existing request/database lifecycle.

If any step fails, the transaction rolls back, preventing a partially registered tenant.

## Version
Backend and OpenAPI version: **0.2.7**.

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

