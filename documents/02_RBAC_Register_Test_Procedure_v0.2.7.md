# RBAC Registration Test Procedure v0.2.7

## 1. Start backend

```powershell
cd C:\Users\Ali\Downloads\backend
uvicorn app.main:app --reload
```

## 2. Verify version
Open Swagger at `/docs`. The title should show **AI Employee Platform 0.2.7**.
The OpenAPI document is available at `/api/v1/openapi.json`.

## 3. Register a fresh tenant
Use a new slug and a plain email value:

```json
{
  "tenant_name": "Test Tenant RBAC 027",
  "tenant_slug": "test-tenant-rbac-027",
  "email": "rbac.test027@example.com",
  "password": "Test123456!",
  "full_name": "RBAC Test User"
}
```

Important: enter the email as plain text. Do not paste Markdown such as `[email](mailto:email)`.

## 4. Expected result
The request must no longer return the previous `Insert.on_conflict_do_nothing` AttributeError. A successful registration should return the normal registration response and the server log should not contain a traceback.

## 5. Database checks
The registration transaction should contain:
- one tenant with the requested slug;
- one first user marked as tenant administrator/superuser;
- one tenant-scoped `Admin` role;
- Core permissions: `employee.read`, `employee.write`, `run.read`, `run.execute`, `file.read`, `file.write`, `audit.read`;
- corresponding `role_permissions` rows;
- one `user_roles` row;
- registration/role-assignment audit records.

## 6. Regression signal
The old error is:

```text
AttributeError: 'Insert' object has no attribute 'on_conflict_do_nothing'
```

Seeing this error means the backend is still running an old `auth_service.py` or the wrong `insert` import remains.

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

