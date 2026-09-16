# Stage 8 Governance Audit Checklist

**Date:** 2026-09-16  
**Audit baseline:** `1c8c3ee2fc933148f90e967e18167fe602d0ad00`  
**Acceptance evidence:** `docs/engineering/STAGE_8_ACCEPTANCE_EVIDENCE_2026-09-16.md`

## Purpose

This checklist reconciles Stage 8 design requirements with repository implementation, automated validation and evidence boundaries. It supersedes the earlier checkpoint where replacement governance and workflow principal propagation were still listed as implementation gaps.

## Current verified repository evidence

- [x] Backend validation suite: **775 passed**.
- [x] Agent/workflow focused validation: **229 passed, 546 deselected**.
- [x] Workflow state-machine enforcement is implemented and validated.
- [x] AgentInstance lifecycle states and transition enforcement are implemented.
- [x] AgentInstance retirement is terminal and direct activation is blocked from the generic lifecycle path.
- [x] AgentInstance lifecycle API records actor/requester attribution.
- [x] Agent identity is first-class and tenant-scoped; access-review enforcement exists.
- [x] Policy decisions are connected to the audit bridge (PR #514).
- [x] Governed AgentInstance replacement workflow is implemented and tested (PR #516).
- [x] AgentInstance principal identity is preserved through workflow child-run creation (PR #517).
- [x] Agent-to-agent delegation is governed by explicit delegation proof and policy validation.
- [x] Tool allow-list and permission checks are enforced by the policy/tool execution path.
- [x] Approval binding checks tenant, run, tool, tool-call identity and arguments in the governed approval path.
- [x] Tenant fairness/resource-cap runtime evidence exists for the current engineering scope.
- [x] Bounded Tool Calling / Structured Arguments / Multi-step runtime mechanics exist.
- [x] Engineering evidence is kept separate from release/external production evidence.

## Governance boundary audit

### Lifecycle

- [x] Lifecycle transition enforcement exists and has validation coverage.
- [x] Agent governance migrations and API surfaces are present.
- [x] Full AgentInstance lifecycle evidence is mapped to implementation files.
- [x] Retirement governance is terminal and disables execution.
- [x] Replacement is a distinct governed workflow with explicit lineage and cutover controls.

### Identity and authorization

- [x] AgentIdentity is a first-class tenant-scoped principal.
- [x] Policy decisions are mapped to execution-trace metadata by the policy audit bridge.
- [x] Workflow child runs preserve the parent `agent_instance_id` evidence boundary.
- [x] Agent-to-agent delegation requires an explicit delegation proof and is denied when identity/access-review conditions fail.
- [x] Per-action policy evaluates lifecycle, identity, access review, delegation, tool and permission conditions.

### Tool governance

- [x] Tool allow-list enforcement exists in both policy admission and governed execution.
- [x] Side-effecting tool execution is subject to the governed policy/permission boundary.
- [x] High-risk approval binding is fail-closed when approval context is missing, mismatched or stale.
- [x] Approved tool continuation is bound to the original run/tool-call/arguments and re-authorized in the worker.

### Auditability

- [x] Policy decisions, lifecycle transitions and run principal propagation have explicit audit evidence.
- [x] Correlation metadata includes tenant/run/tool/delegation context where those contexts exist.
- [x] Audit bridge failures do not alter authorization behavior.
- [ ] Independent external audit-system durability/immutability verification.

### Economics and safety

- [x] Usage/cost infrastructure and tenant-scoped optimization surfaces exist.
- [x] Execution quotas and resource-limit infrastructure exist.
- [x] Tenant fairness/resource-cap runtime evidence is covered by Phase 14.12 runtime tests.
- [x] Bounded multi-step execution has an explicit iteration limit.
- [ ] Production billing/operations acceptance on the deployed target.
- [ ] Production SLO/SLI and error-budget measurements.

### Evaluation and publication

- [x] Evaluation/publication concepts and lineage infrastructure exist in the repository.
- [ ] Independent production certification of evaluation gates for every required risk tier.
- [ ] Exact-SHA certification for a promoted post-v1.4.1 release.

## Evidence mapping

| Requirement | Current evidence | Status |
|---|---|---|
| Explicit lifecycle states | `backend/app/models/agent_instance.py` → `AgentInstanceStatus` | Verified |
| Fail-closed transitions | `backend/app/services/agent_template_service.py` → `_ALLOWED_LIFECYCLE_TRANSITIONS` | Verified |
| Governed lifecycle mutation | `transition_instance` + lifecycle tests | Verified |
| Terminal retirement | `RETIRED` has no outgoing transitions; execution disabled | Verified |
| Replacement workflow | `backend/app/services/agent_workforce_replacement_service.py`; PR #516 | Verified |
| Lifecycle audit attribution | `agent_instance.lifecycle_changed` | Verified |
| First-class identity | `backend/app/models/agent_identity.py` | Verified |
| Policy decision audit | `agent_policy_engine.authorize` → `agent_policy_audit.py`; PR #514 | Verified |
| Workflow principal propagation | `Run.agent_instance_id`; PR #517 | Verified |
| Agent-to-agent trust | `agent_delegation_service.py` + policy engine + delegation governance tests | Verified for repository scope |
| Tool governance | policy engine + Tool Registry + approval service | Verified for governed execution paths |
| Usage/budget controls | usage/optimization APIs, quotas and budget policy fields | Engineering implemented; production validation external |
| Runtime capacity/fairness | Phase 14.12 / 14.13 runtime evidence tests | Verified for engineering scope |

## Remaining gates

These are not missing Stage 8 foundation components. They are evidence/certification gates that cannot be truthfully closed by local unit tests alone:

1. Production deployment identity and target evidence.
2. Measured production SLO/SLI/error budget.
3. Real backup/restore/DR RPO/RTO.
4. Live provider acceptance on the deployed target.
5. Deployed Vendor → Reseller → Client isolation/RBAC.
6. Deployed-target DAST and independent security review.
7. Networking/TLS/secret lifecycle evidence.
8. HA/failure recovery and incident/on-call rehearsal.
9. Final customer acceptance.
10. Fresh exact-SHA release certification for any promoted commit after certified `v1.4.1`.

## Reconciliation result

**Stage 8 engineering foundation: implemented and validated for the repository scope.**

The remaining production items are deliberately retained as gates rather than being marked complete by inference. The companion acceptance-evidence document records the concrete repository tests and implementation surfaces supporting this conclusion.
