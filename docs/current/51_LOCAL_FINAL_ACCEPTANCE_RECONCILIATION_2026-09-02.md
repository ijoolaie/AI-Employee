# Local Final Acceptance Reconciliation — 2026-09-02

## Purpose

Record the local production-like acceptance work completed on 2026-09-02 so completed gates are not unnecessarily repeated. This document is local/engineering evidence only and does not certify an external production environment.

## Canonical evidence boundary

The current repository delivery scope is local production-like validation followed by customer delivery. External production, Vendor, Reseller and customer-environment acceptance remain separate evidence events.

## Completed local Product Acceptance gates

The following repository certification scripts were executed successfully against the local Docker stack:

| Gate | Result | Evidence |
|---|---|---|
| Tenant Isolation + RBAC + Knowledge P0 | PASS | `scripts/e2e_tenant_rbac_verify.py` — executed twice; both runs passed and cleaned 2 certification tenants |
| Conversation Tenant Isolation P0 | PASS | `scripts/e2e_conversation_tenant_verify.py` |
| Employee → Run → AI → Result | PASS | `scripts/e2e_employee_run_verify.py` |
| Files → Knowledge → Memory | PASS | `scripts/e2e_files_knowledge_memory_verify.py` |
| Admin / Developer API Keys | PASS | `scripts/e2e_admin_developer_verify.py` |
| Workflow + Approval + Schedule | PASS | `scripts/e2e_workflow_approval_schedule_verify.py` |

The final workflow gate explicitly passed: `WORKFLOW + APPROVAL + SCHEDULE PRODUCT ACCEPTANCE CERTIFICATION PASS`.

These six gates are considered **completed for the current local acceptance cycle**. Do not rerun them merely to reproduce this status. Rerun only for a regression, material code/configuration change affecting the gate, new release identity, or a documented environment reset that invalidates the evidence.

## Tenant fixture cleanup incident and resolution

The Tenant/RBAC certification initially created repeated fixtures and polluted the local database. The observed legacy fixture pattern was `security-a-*` / `security-b-*`, with 94 tenants in each group at the time of diagnosis.

The cleanup helper originally recognized only `cert-a-*` / `cert-b-*`. PR #212 aligned the helper with both known certification naming patterns and also removed sensitive response-body/exception logging from the certification script to address CodeQL findings.

Local cleanup was then executed successfully and verified with SQL showing:

`remaining_security_tenants = 0`

The official Tenant/RBAC/Knowledge certification was subsequently executed twice, and both runs passed and cleaned their two newly created certification tenants.

## Docker Compose / Beat incident and resolution

The Workflow + Approval + Schedule certification initially failed because the expected pending approval was not created.

Runtime diagnosis established that the local Compose services were split across two Docker networks:

- `beat` → `ai-employee_backend` (`172.21.0.0/16`)
- `redis`, `worker`, `api`, `postgres` → `ai-employee_default` (`172.18.0.0/16`)

Inside `beat`, `getent hosts redis` returned no address, while Beat logs showed `Name or service not known` for `redis:6379`. The repository Compose configuration itself did not show an intentional network split; this was a stale/mismatched local Docker network state.

The Compose stack was reconciled without deleting volumes. After recovery, the Workflow + Approval + Schedule certification passed completely, including approval creation, approval, workflow resume, schedule creation/next-run, tenant read, deactivation and deletion.

Do not treat this historical Docker network incident as an application-code defect. If the same symptom recurs, inspect Compose network membership/DNS before changing application code or database state.

## PR / repository fixes completed

- PR #211: tenant/RBAC certification fixture cleanup was merged.
- PR #212: `fix: align tenant fixture cleanup and CodeQL logging` was merged.
- PR #212 merge commit: `bc51ac51fcd16e0b2dd63071d28d74a56afc8866`.
- The current `main` therefore contains the cleanup-prefix compatibility and safe logging fixes.

## Test execution contract

Use the repository's certification scripts with:

`docker compose exec -T api sh -lc 'cd /app && PYTHONPATH=/app python scripts/<script>.py'`

For the standalone cleanup helper, the import path must be supplied explicitly when invoking it directly:

`docker compose exec -e PYTHONPATH=/app api python /app/scripts/cleanup_e2e_tenant_rbac_fixtures.py`

The helper is dry-run by default; destructive cleanup requires its explicit apply mode.

## Remaining local acceptance frontier

The completed Product Acceptance gates above are not the next work item. The remaining local acceptance work follows the existing Production Candidate Readiness and Current State Reconciliation documents:

1. local production hardening/security validation
2. local observability/monitoring contract validation, including explicit external-alert-provider limitation
3. local backup/restore and DR reconciliation for the candidate identity
4. controlled local rollback reconciliation
5. final local health/readiness/product smoke verification where not already covered by the recorded gates
6. one final local evidence manifest binding version, exact SHA, migration head and artifact checksums
7. customer delivery package and handoff documentation

## External evidence remains separate

The following remain unproven and must not be inferred from this local evidence:

- external production deployment
- external monitoring/alert delivery
- external target recovery/DR and rollback
- live payment/provider certification
- live WhatsApp outbound provider certification
- Vendor → Reseller → Client production acceptance
- customer-environment acceptance
- commercial go-live

## Repetition rule

A completed local gate is a reusable evidence checkpoint. Do not repeat a completed certification solely because the conversation has moved to another step. Repeat it only when a defined invalidation condition exists: regression, relevant implementation/configuration change, new release/candidate SHA, materially changed environment, or explicit recovery of an invalidated evidence store.
