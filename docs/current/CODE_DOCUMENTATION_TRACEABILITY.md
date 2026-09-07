# Code ↔ Documentation Traceability Matrix

**Date:** 2026-09-07
**Status:** ACTIVE AUDIT BASELINE

This matrix distinguishes implemented repository foundations from architecturally planned product surfaces. A blueprint entry is never sufficient evidence for an AS-BUILT claim.

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
| AgentDefinition | `backend/app/models/agent_definition.py`, `phase8_01_execution_foundation.py` | existing execution services; dedicated definition governance remains partial | FOUNDATION IMPLEMENTED / PARTIAL API |
| AgentTemplate | `backend/app/models/agent_template.py`, `p8_04_agent_governance_foundation.py` | `backend/app/api/v1/agent_templates.py` + lifecycle service + RBAC permissions | GOVERNANCE API IMPLEMENTED / EVALUATION GATE PENDING |
| AgentInstance | `backend/app/models/agent_instance.py`, `p8_04_agent_governance_foundation.py` | governed provisioning and `/agent-templates/agent-instances/{id}/lifecycle` endpoint | PROVISIONING + LIFECYCLE API IMPLEMENTED / E2E GATES PENDING |
| Agent identity / sponsorship | `AgentInstance.sponsor_user_id`, permission/approval policy and risk tier | provisioning requires attributable sponsor + approver; access-review UI/API pending | FOUNDATION IMPLEMENTED / ACCESS-REVIEW GAP |
| WorkItem | existing WorkItem model and execution services | execution APIs/UI | AS-BUILT / VERIFY GATES |
| HumanExecutor abstraction | V1.5 architecture specification | existing users/employees are compatibility candidates | PLANNED |
| Human ↔ Agent delegation | V1.5 specification | no canonical implementation evidence established | PLANNED |
| Agent ↔ Agent handoff | V1.5 specification | no canonical implementation evidence established | PLANNED |
| Policy-driven approvals | existing workflow/approval concepts plus AgentInstance approval policy | template publish/provision/lifecycle gates exist; unified action-level enforcement requires more API/test coverage | PARTIAL / GAP |
| Scoped Agent tools | V1.5 specification; existing integration/tool surfaces | developer/API surfaces exist | PARTIAL / GAP |
| Platform / Reseller / Client workspace separation | workspace-related code/docs | customer/developer/report routes exist | PARTIAL / AUDIT |
| Test Center | Phase 12 evidence | authorized UI/API and persisted evidence | IMPLEMENTED / OPERATIONAL HARDENING |
| Usage / cost attribution | existing usage/billing concepts | usage/billing surfaces | PARTIAL; workforce attribution remains PLANNED |
| Agent teams | Phase 13 architecture/engineering evidence | TeamDefinition/TeamVersion/TeamInstallation/Marketplace evidence | ENGINEERING COMPLETE / EXTERNAL ACCEPTANCE SEPARATE |

## Important interpretation rule

The repository has two different kinds of Agent truth:

1. **V1.5 architecture truth** — defines the target Human + Agent operating model and contracts.
2. **Phase engineering truth** — records which concrete capabilities have actually been implemented and tested.

These must not be merged into one claim. The Stage 8 governance foundation and first customer-facing API gate are real repository implementation, but evaluation, access-review, tool authorization, UI and end-to-end evidence remain separate gates.

## Current architecture truth

- V1.4 remains the frozen architecture foundation.
- V1.5 is the Agentic Operating Model architecture/documentation baseline.
- The current certified product release remains `v1.3.8` at exact commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- Stage 8 implementation is active with governed `AgentDefinition → AgentTemplate → AgentInstance` persistence and lifecycle/provisioning API surfaces.
- Phase 11–14 engineering status is tracked separately from release certification.

## Implementation frontier

The next implementation gates are explicit:

1. Add a first-class AgentTemplate evaluation API/evidence contract instead of relying only on the persisted `evaluation_policy.passed` flag.
2. Add agent identity/access-review records and scheduled/reviewed authorization state.
3. Bind template permission/approval policy to actual tool invocation authorization.
4. Add Workforce Registry and governance UI.
5. Add customer installation/e2e tests covering tenant isolation, sponsorship, approval attribution and lifecycle transitions.
6. Add dynamic workforce proposal → Board review → CEO approval workflow.

## Evidence rule

A capability is marked **AS-BUILT** or **IMPLEMENTED** only when code, API/UI and relevant tests/evidence can be identified. Architecture prose alone is classified as **PLANNED** or **TARGET ARCHITECTURE**. Repository model/migration work is reported as a foundation implementation, not as complete customer-facing product functionality.
