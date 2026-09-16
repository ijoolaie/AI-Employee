# Stage 8 Governance Audit Checklist

**Date:** 2026-09-16
**Audit baseline:** `main` at `1c8c3ee2fc933148f90e967e18167fe602d0ad00`

## Purpose

This checklist tracks reconciliation between Stage 8 design requirements, repository implementation, automated validation and evidence. It supersedes the earlier 2026-09-15 checkpoint where replacement governance and workflow principal propagation were still listed as open implementation gaps.

## Current verified repository evidence

- [x] Backend validation suite completed: **775 passed**.
- [x] Agent/workflow focused validation completed: **229 passed, 546 deselected**.
- [x] Workflow state-machine enforcement is implemented and validated.
- [x] AgentInstance lifecycle states are explicitly modeled and transition enforcement is implemented.
- [x] AgentInstance retirement is terminal and direct activation is blocked from the generic lifecycle path.
- [x] AgentInstance lifecycle API records actor/requester attribution in `agent_instance.lifecycle_changed` audit events.
- [x] Agent identity is first-class and tenant-scoped; access-review enforcement exists.
- [x] Policy decisions are connected to the audit bridge (PR #514).
- [x] Governed AgentInstance replacement workflow is implemented and tested (PR #516).
- [x] AgentInstance principal identity is preserved through workflow child-run creation (PR #517).
- [x] Engineering evidence remains separate from release/external production evidence.

## Governance boundary audit

### Lifecycle

- [x] Lifecycle transition enforcement exists and has validation coverage.
- [x] Agent governance foundation migrations and API surfaces are present.
- [x] Full AgentInstance lifecycle evidence is mapped to implementation files.
- [x] Retirement governance is terminal and disables execution.
- [x] Replacement is a distinct governed workflow with explicit lineage and cutover controls.

### Identity and authorization

- [x] AgentIdentity is a first-class tenant-scoped principal.
- [x] Policy decisions are mapped to execution-trace metadata by the policy audit bridge.
- [x] Workflow child runs preserve the parent `agent_instance_id` evidence boundary.
- [ ] Every protected agent action has independently reconciled principal identity evidence.
- [ ] Agent-to-agent trust boundary acceptance tests are complete.

### Tool governance

- [ ] Complete evidence package for tool allow-list enforcement across all protected execution paths.
- [ ] Complete evidence package proving every side-effecting action receives policy evaluation.
- [ ] Complete end-to-end approval binding evidence for high-risk tool actions.

### Auditability

- [ ] Every execution path has complete correlation and actor/principal attribution evidence.
- [ ] Audit records are demonstrated append-oriented and protected from ordinary agent mutation across the full Stage 8 surface.

### Economics and safety

- [ ] Usage attribution is reconciled to tenant/agent/work item across all execution paths.
- [ ] Hard budget enforcement acceptance tests are complete for all required scopes.
- [ ] Runaway execution protection evidence is complete for the governed autonomous surface.

### Evaluation and publication

- [ ] Evaluation gates are demonstrated to block unsafe publication for every required risk tier.
- [ ] Publication/version lineage evidence is reconciled to the exact implementation SHA.

## Evidence mapping updates

| Requirement | Current evidence | Status |
|---|---|---|
| Explicit lifecycle states | `backend/app/models/agent_instance.py` → `AgentInstanceStatus` | Verified |
| Fail-closed transitions | `backend/app/services/agent_template_service.py` → `_ALLOWED_LIFECYCLE_TRANSITIONS` | Verified |
| Governed lifecycle mutation | `transition_instance` + lifecycle tests | Verified |
| Terminal retirement | `RETIRED` has no outgoing transitions; execution disabled | Verified |
| Replacement workflow | `backend/app/services/agent_workforce_replacement_service.py`; replacement API; PR #516 | Implemented / tests passed |
| Lifecycle audit attribution | `agent_instance.lifecycle_changed` audit event | Verified |
| First-class identity | `backend/app/models/agent_identity.py` | Verified |
| Policy decision audit | `agent_policy_engine.authorize` → policy audit bridge; PR #514 | Implemented / tests present |
| Workflow principal propagation | `Run.agent_instance_id` preserved for child runs; PR #517 | Implemented / tests passed |
| Agent-to-agent trust | Delegation/policy primitives exist | Acceptance evidence open |
| Tool governance | Registry/policy controls exist | Evidence reconciliation open |
| Usage/budget controls | Usage/cost infrastructure exists | Acceptance evidence open |

## Reconciliation result

The previous checklist status is now stale in three important places: replacement governance is no longer an implementation gap; workflow child principal propagation is implemented; and the repository validation baseline is 775 passing rather than 759.

Stage 8 is therefore best described as **governed workforce foundation implemented with remaining acceptance/evidence gaps**, not as an unimplemented foundation and not yet as fully certified Stage 8.

## Next engineering sequence

1. Finish principal-identity evidence reconciliation across every protected execution path.
2. Audit tool allow-list, side-effect and approval-binding paths against the governance checklist.
3. Finish agent-to-agent trust acceptance tests and audit evidence.
4. Close risk-tier, evaluation-gate, usage/budget and runaway-execution evidence gaps.
5. Update exact-commit traceability.
6. Run fresh exact-SHA release certification before promoting Agent capability code.
7. Keep Stage 7 production claims blocked until real deployment evidence exists.
