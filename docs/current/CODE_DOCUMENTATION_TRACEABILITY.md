# Code ↔ Documentation Traceability Matrix

**Date:** 2026-08-27
**Status:** ACTIVE AUDIT BASELINE

This matrix distinguishes what is implemented in the repository from what is architecturally planned.

| Capability | Code evidence | UI/API evidence | Current status |
|---|---|---|---|
| Tenant / multi-tenancy | employee/run and tenant-aware modules; migrations | tenant/auth/workspace surfaces | AS-BUILT / VERIFY GATES |
| RBAC / permissions | employee and authorization modules | role-aware routes | AS-BUILT / VERIFY GATES |
| Employee execution | `backend/app/models/employee.py`, `backend/app/models/run.py` | customer employee/run pages | AS-BUILT |
| Workflow | workflow schemas/modules and UI surfaces | workflow APIs/UI | AS-BUILT / PARTIAL |
| Memory | `backend/app/models/memory.py`, schema | memory-related surfaces | AS-BUILT |
| Conversations / inbox | conversation model, channel webhook | chat/inbox surfaces | AS-BUILT |
| Traces / observability | traces UI and run infrastructure | traces page | AS-BUILT / VERIFY |
| AgentDefinition | V1.5 architecture specification | no canonical implementation evidence yet | PLANNED |
| AgentInstance | V1.5 architecture specification | no canonical implementation evidence yet | PLANNED |
| WorkItem | V1.5 architecture specification | no canonical implementation evidence yet | PLANNED |
| HumanExecutor abstraction | V1.5 architecture specification | existing users/employees provide compatibility candidates | PLANNED |
| Human ↔ Agent delegation | V1.5 specification | no canonical implementation evidence yet | PLANNED |
| Agent ↔ Agent handoff | V1.5 specification | no canonical implementation evidence yet | PLANNED |
| Policy-driven approvals | existing workflow/approval concepts require unified execution integration | UI/API evidence requires deep audit | PARTIAL / GAP |
| Scoped Agent tools | V1.5 specification; existing integration/tool surfaces | developer/API surfaces exist | PARTIAL / GAP |
| Platform / Reseller / Client workspace separation | workspace-related branches/docs and existing customer routes | customer/developer/report routes exist | PARTIAL / AUDIT |
| Test Center in all workspaces | V1.5 specification | canonical implementation evidence not yet established | PLANNED |
| Usage / cost attribution to WorkItem | existing usage/billing concepts | usage/billing surfaces | PARTIAL; WorkItem attribution PLANNED |
| Agent teams | V1.5 specification | no canonical implementation evidence yet | PLANNED |

## Evidence rule

A capability is not marked AS-BUILT merely because it appears in a blueprint. Code, API/UI and relevant tests must be identified.

## Current architecture truth

V1.4 remains the frozen baseline. V1.5 defines the Human + Agent extension: one WorkItem can be executed by a Human, specialized Agent, or both, with shared authorization, tools, approvals and audit contracts. See `docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`.

## Immediate implementation frontier

1. Define WorkItem persistence and contracts.
2. Define executor abstraction and HumanExecutor compatibility adapter.
3. Define AgentDefinition / AgentInstance persistence and lifecycle.
4. Add execution/delegation/handoff state machine.
5. Bind authorization, tool policy, approval and audit to WorkItem execution.
6. Add tests and Test Center contracts before broad workspace UI expansion.
