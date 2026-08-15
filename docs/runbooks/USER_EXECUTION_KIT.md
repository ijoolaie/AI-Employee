# AI Employee Platform — User Execution Kit (RC8)

This kit gives each supported user persona a short, copy/paste-ready execution path.

| Persona | Account model | Entry point | Script |
|---|---|---|---|
| Tenant Admin | First registered tenant user; receives tenant `Admin` role | `/dashboard` | `scripts/personas/tenant-admin.ps1` |
| Tenant Operator | Tenant user with explicitly configured Operator permissions | `/dashboard` | `scripts/personas/tenant-operator.ps1` |
| Platform Admin | Existing active user explicitly promoted with `is_platform_admin=true` | `/admin` | `scripts/personas/platform-admin.ps1` |
| B2C Customer | Public channel customer; no platform account | Public chat URL/widget | `scripts/personas/b2c-customer.ps1` |

> The application guarantees the first tenant user as `Admin`. Operator provisioning remains an explicit RBAC operation. Platform Admin is separate from tenant Admin.

## One-time setup

From repository root in PowerShell:

```powershell
.\scripts\bootstrap.ps1
```

## Tenant Admin

```powershell
.\scripts\personas\tenant-admin.ps1 -Register
```

Or, if the tenant already exists:

```powershell
.\scripts\personas\tenant-admin.ps1
```

The script checks API health, authenticates, calls `/auth/me`, and prints the dashboard URL.

## Tenant Operator

```powershell
.\scripts\personas\tenant-operator.ps1 -TenantSlug demo -Email operator@demo.com -Password 'ChangeMe123!'
```

This script authenticates an existing user. It deliberately does not invent or silently grant an Operator role. Configure the tenant RBAC role explicitly.

## Platform Admin

```powershell
.\scripts\personas\platform-admin.ps1 -TenantSlug demo -Email admin@demo.com
```

This uses the project's explicit promotion utility. Tenant Admin/superuser status alone does not imply platform-admin status.

## B2C Customer

```powershell
.\scripts\personas\b2c-customer.ps1 -PublicChatUrl 'http://localhost:3000/chat/public/<channel-key>'
```

B2C customers do not need a platform login. Verify conversation creation, customer message, AI response, and persisted conversation.

## Runtime

For a local non-Docker process layout:

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app worker -l info --pool=solo

# Terminal 3
cd frontend
npm run dev
```

For Docker-first operation, use `docker compose` and confirm PostgreSQL/Redis are healthy before API/worker certification.

## Safety

- Never commit real secrets.
- Never infer platform-admin access from tenant-admin access.
- Never treat B2C browser-supplied tenant IDs as authority.
- Run scripts from repository root.
