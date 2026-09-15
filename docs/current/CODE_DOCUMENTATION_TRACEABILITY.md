# Code ↔ Documentation Traceability Matrix

**Date:** 2026-09-15
**Status:** ACTIVE AUDIT BASELINE

This matrix distinguishes implemented repository foundations from architecturally planned product surfaces. A blueprint entry is never sufficient evidence for an AS-BUILT claim.

## Capability status

| Capability | Code evidence | UI/API evidence | Current status |
|---|---|---|---|
| Tenant / multi-tenancy | tenant-aware modules and migrations | tenant/auth/workspace surfaces | AS-BUILT / VERIFY GATES |
| RBAC / permissions | authorization modules | role-aware routes | AS-BUILT / VERIFY GATES |
| Employee execution | `backend/app/models/employee.py`, `backend/app/models/run.py` | customer employee/run pages | AS-BUILT |
| Workflow | workflow schemas/modules and UI surfaces | workflow APIs/UI | AS-BUILT / PARTIAL |
| Workflow state governance | workflow state machine implementation + transition validation tests | execution path validation | IMPLEMENTED / VALIDATION PASSED |
| Memory | `backend/app/models/memory.py`, schema | memory-related surfaces | AS-BUILT |
| Conversations / inbox | conversation model, channel webhook | chat/inbox surfaces | AS-BUILT |
| AgentDefinition | `backend/app/models/agent_definition.py`, execution foundation migrations | existing execution services; dedicated definition governance remains partial | FOUNDATION IMPLEMENTED / PARTIAL API |
| AgentTemplate | `backend/app/models/agent_template.py` | template governance APIs | GOVERNANCE API IMPLEMENTED / E2E GATES PENDING |
| AgentInstance | `backend/app/models/agent_instance.py` | provisioning and lifecycle endpoints | PROVISIONING + LIFECYCLE IMPLEMENTED / E2E GATES PENDING |
| Agent identity / sponsorship | identity/access-review models | identity and review APIs | ENFORCEMENT IMPLEMENTED / UI + E2E PENDING |
| Agent execution authorization | governance services + worker checks | ToolRegistry boundary | IMPLEMENTED / E2E GATES PENDING |
| Workforce Registry | registry projection over governed agents | governance registry API | API IMPLEMENTED / UI PENDING |
| Test Center | persisted test execution evidence | authorized APIs | IMPLEMENTED / OPERATIONAL HARDENING |

## Stage 8 validation record

Current verified engineering evidence:

- Backend validation suite: `759 passed`.
- Workflow state-machine enforcement branch validated.
- Pytest configuration reconciliation completed.
- Test warning cleanup completed except remaining intentional/non-blocking marks where applicable.

## Governance interpretation rule

The repository maintains separation between:

1. Architecture intent.
2. Implemented repository capability.
3. Production certification evidence.

A capability is not considered production-certified only because a model, migration, or API exists. Required evidence includes implementation path, tests, authorization boundaries and operational validation.

## Remaining governance gates

1. Complete lifecycle evidence mapping for AgentInstance including retirement and replacement flows.
2. Map protected agent actions to principal identity and authorization decision records.
3. Expand ToolRegistry enforcement evidence for revocation, expiry, retirement, tenant isolation and allow-list denial.
4. Add customer-facing end-to-end governance scenarios.
5. Continue reconciliation of issues, actions and engineering documents before new capability claims.

## Evidence rule

A capability is marked IMPLEMENTED only when code paths and validation evidence are identifiable. Architecture documents remain target-state references unless backed by repository evidence.
