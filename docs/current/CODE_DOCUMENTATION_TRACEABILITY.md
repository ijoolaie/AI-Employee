# Code ↔ Documentation Traceability Matrix

**Date:** 2026-09-07
**Status:** ACTIVE AUDIT BASELINE

This matrix distinguishes what is implemented in the repository from what is architecturally planned. A blueprint entry is never sufficient evidence for an AS-BUILT claim.

## Capability status

| Capability | Code evidence | UI/API evidence | Current status |
|---|---|---|---|
| Tenant / multi-tenancy | tenant-aware modules and migrations | tenant/auth/workspace surfaces | AS-BUILT / VERIFY GATES |
| RBAC / permissions | authorization modules | role-aware routes | AS-BUILT / VERIFY GATES |
| Employee execution | `backend/app/models/employee.py`, `backend/app/models/run.py` | customer employee/run pages | AS-BUILT |
| Workflow | workflow schemas/modules and UI surfaces | workflow APIs/UI | AS-BUILT / PARTIAL |
| Memory | `backend/app/models/memory.py`, schema | memory-related surfaces | AS-BUILT |
| Conversations / inbox | conversation model, channel webhook | chat/inbox surfaces | AS-BUILT |
| Traces / observability | traces UI and run infrastructure | traces page | AS-BUILT / VERIFY |
| AgentDefinition | V1.5 architecture specification | no canonical implementation evidence established by this matrix | PLANNED |
| AgentInstance | V1.5 architecture specification | no canonical implementation evidence established by this matrix | PLANNED |
| WorkItem | V1.5 architecture specification | no canonical implementation evidence established by this matrix | PLANNED |
| HumanExecutor abstraction | V1.5 architecture specification | existing users/employees are compatibility candidates | PLANNED |
| Human ↔ Agent delegation | V1.5 specification | no canonical implementation evidence established | PLANNED |
| Agent ↔ Agent handoff | V1.5 specification | no canonical implementation evidence established | PLANNED |
| Policy-driven approvals | existing workflow/approval concepts | unified execution evidence requires audit | PARTIAL / GAP |
| Scoped Agent tools | V1.5 specification; existing integration/tool surfaces | developer/API surfaces exist | PARTIAL / GAP |
| Platform / Reseller / Client workspace separation | workspace-related code/docs | customer/developer/report routes exist | PARTIAL / AUDIT |
| Test Center | Phase 12 evidence | authorized UI/API and persisted evidence | IMPLEMENTED / OPERATIONAL HARDENING |
| Usage / cost attribution | existing usage/billing concepts | usage/billing surfaces | PARTIAL; WorkItem attribution remains PLANNED |
| Agent teams | Phase 13 architecture/engineering evidence | TeamDefinition/TeamVersion/TeamInstallation/Marketplace evidence | ENGINEERING COMPLETE / EXTERNAL ACCEPTANCE SEPARATE |

## Important interpretation rule

The repository has **two different kinds of Agent truth**:

1. **V1.5 architecture truth** — defines the target Human + Agent operating model and contracts.
2. **Phase engineering truth** — records which concrete capabilities have actually been implemented and tested.

These must not be merged into one claim. In particular, the existence of `V1.5_AGENTIC_OPERATING_MODEL.md` does not mean every V1.5 abstraction is already implemented.

## Current architecture truth

- V1.4 remains the frozen architecture foundation.
- V1.5 is the Agentic Operating Model architecture/documentation baseline.
- The current certified product release remains `v1.3.8` at exact commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- Phase 11–14 engineering status is tracked separately from release certification.

## Implementation frontier

Where V1.5 capabilities are still marked PLANNED/PARTIAL, implementation should proceed through explicit engineering phases with code, API/UI and test evidence before the capability is promoted to AS-BUILT.

1. Define WorkItem persistence and contracts.
2. Define executor abstraction and HumanExecutor compatibility adapter.
3. Define AgentDefinition / AgentInstance persistence and lifecycle.
4. Add execution/delegation/handoff state machine.
5. Bind authorization, tool policy, approval and audit to WorkItem execution.
6. Add tests and Test Center contracts before broad workspace UI expansion.

## Evidence rule

A capability is marked **AS-BUILT** or **IMPLEMENTED** only when code, API/UI and relevant tests/evidence can be identified. Architecture prose alone is classified as **PLANNED** or **TARGET ARCHITECTURE**.
