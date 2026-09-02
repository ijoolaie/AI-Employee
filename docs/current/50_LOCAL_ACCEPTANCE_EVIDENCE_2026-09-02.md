# Local Acceptance Evidence — 2026-09-02

## Purpose

This record preserves the local production-like acceptance work completed during the 2026-09-02 validation cycle so the same gates and diagnostics do not need to be repeated merely to rediscover prior evidence.

**Evidence class:** LOCAL / REAL-STACK

This document is not external production certification and does not establish live Stripe, WhatsApp, customer, Vendor, Reseller, or external deployment acceptance.

## Repository identity

- Repository: `ijoolaie/AI-Employee`
- Branch validated by the local stack: `main`
- Main commit at the end of this cycle: `bc51ac51fcd16e0b2dd63071d28d74a56afc8866`
- Date: 2026-09-02

## Product acceptance gates completed

The following official repository certification scripts were executed successfully against the local Docker production-like stack.

### 1. Tenant Isolation + RBAC + Knowledge — P0

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_tenant_rbac_verify.py'
```

Result:

```text
TENANT ISOLATION + RBAC + KNOWLEDGE P0 REAL-STACK CERTIFICATION PASS
CERTIFICATION FIXTURE CLEANUP PASS tenants=2
```

The same certification was executed twice in this cycle and both runs passed and cleaned their two temporary tenants.

### 2. Conversation Tenant Isolation — P0

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_conversation_tenant_verify.py'
```

Result:

```text
CONVERSATION TENANT ISOLATION P0 REAL-STACK CERTIFICATION PASS
```

Covered public conversation create/read, authenticated cross-tenant list isolation, wrong-customer token rejection, cross-tenant public read rejection, and cross-tenant handoff rejection.

### 3. Employee → Run → AI → Result

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_employee_run_verify.py'
```

Result:

```text
PRODUCT ACCEPTANCE EMPLOYEE -> RUN -> AI -> RESULT PASS
```

Covered authentication, commercial-license fixture, employee create/version/list/get, run creation, and terminal result.

### 4. Files → Knowledge → Memory

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_files_knowledge_memory_verify.py'
```

Result:

```text
PRODUCT ACCEPTANCE FILES -> KNOWLEDGE -> MEMORY PASS
```

Covered file upload/list/get/download, knowledge index/search, and memory create/search.

### 5. Admin / Developer API Keys

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_admin_developer_verify.py'
```

Result:

```text
PRODUCT ACCEPTANCE ADMIN / DEVELOPER PASS
```

Covered platform-admin denial for non-platform users, developer API-key creation, secret redaction, and revoke.

### 6. Workflow + Approval + Schedule

Command:

```powershell
docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/e2e_workflow_approval_schedule_verify.py'
```

Result:

```text
WORKFLOW CREATE PASS
WORKFLOW VERSION PASS
APPROVAL CREATE PASS
APPROVAL APPROVE PASS
WORKFLOW RESUME COMPLETE PASS
SCHEDULE CREATE NEXT-RUN PASS
SCHEDULE TENANT READ PASS
SCHEDULE DEACTIVATE PASS
SCHEDULE DELETE PASS
WORKFLOW + APPROVAL + SCHEDULE PRODUCT ACCEPTANCE CERTIFICATION PASS
```

## Operational incident found and resolved during acceptance

The first Workflow + Approval + Schedule attempt failed with:

```text
WORKFLOW CREATE PASS
WORKFLOW VERSION PASS
WORKFLOW/APPROVAL/SCHEDULE CERTIFICATION FAIL: pending approval was not created
```

The failure was diagnosed as a Docker Compose network/DNS state issue, not a Workflow implementation defect.

### Diagnosis

`beat` could not resolve `redis` because the containers were attached to different Compose networks:

- `beat` → `ai-employee_backend` (`172.21.0.2`)
- `redis` → `ai-employee_default` (`172.18.0.3`)
- `worker` → `ai-employee_default`
- `api` → `ai-employee_default`

`docker compose exec beat getent hosts redis` returned no address, while Docker's internal resolver was present in `/etc/resolv.conf`.

### Recovery action

The stack was recreated without deleting volumes:

```powershell
docker compose down
docker compose up -d
```

**Important:** `docker compose down -v` was not used; database/storage volumes were preserved.

After recovery, the Workflow certification passed completely as recorded above.

## Tenant/RBAC fixture pollution incident and resolution

An earlier tenant RBAC certification cycle created repeated `Security Tenant A/B` fixtures and polluted the local database. Investigation found approximately 188 legacy security certification tenants (94 A + 94 B) in the local database.

Direct deletion initially encountered expected foreign-key dependencies involving roles, user roles, role permissions, and commercial-license issuer references. The affected commercial-license rows were removed before the security tenants were deleted.

Final verification:

```text
remaining_security_tenants
--------------------------
0
```

The official tenant certification was then rerun twice successfully with automatic cleanup:

```text
CERTIFICATION FIXTURE CLEANUP PASS tenants=2
```

## Fixture cleanup and CodeQL hardening

Two repository fixes were merged before this evidence cycle:

- **PR #211** — added tenant/RBAC certification fixture cleanup.
- **PR #212** — aligned cleanup prefixes with legacy `security-a-*` / `security-b-*` fixtures and removed sensitive response/exception data from CodeQL-visible logging.

PR #212 was merged into `main` at:

`bc51ac51fcd16e0b2dd63071d28d74a56afc8866`

The cleanup helper now recognizes only known certification prefixes:

- `cert-a-*`
- `cert-b-*`
- `security-a-*`
- `security-b-*`

It does not use broad production-unrelated deletion patterns.

## Import-path note for cleanup helper

When running the cleanup helper directly from the mounted `/app/scripts` path, Python may not include `/app` on `sys.path`. The working command is:

```powershell
docker compose exec -e PYTHONPATH=/app api python /app/scripts/cleanup_e2e_tenant_rbac_fixtures.py
```

This produced `Eligible certification tenants: 0` after the local database had been cleaned, confirming no stale eligible fixtures remained.

## Evidence boundary / what this proves

This cycle proves successful local real-stack acceptance for:

- Tenant isolation, RBAC and Knowledge P0
- Conversation tenant isolation P0
- Employee → Run → AI → Result
- Files → Knowledge → Memory
- Admin / Developer API Keys
- Workflow → Approval → Schedule

It also proves the local Docker stack can recover from the observed Compose network mismatch and resume scheduled workflow processing.

It does **not** prove:

- external production deployment
- live payment-provider certification
- live WhatsApp provider certification
- real customer acceptance
- Vendor → Reseller → Customer external acceptance
- commercial go-live

Those remain governed by the existing Phase 5 / Phase 6E external-evidence boundary.

## Do not repeat unless regression evidence appears

Unless code, infrastructure, configuration, migration state, or environment changes invalidate this evidence, these exact local acceptance gates should be treated as already executed and PASS for this validation cycle. Future work should move to the next open roadmap gate or targeted regression rather than rerunning all six gates solely for rediscovery.
