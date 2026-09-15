# Stage 8 Governance Audit Checklist

**Date:** 2026-09-15

## Purpose

This checklist tracks reconciliation between Stage 8 design requirements, repository implementation, tests and evidence.

## Current verified evidence

- [x] Repository validation completed: `759 passed`.
- [x] Workflow state-machine enforcement branch validated locally.
- [x] Test warning cleanup completed through pytest configuration reconciliation.
- [x] Engineering evidence is separated from production certification evidence.
- [x] Workflow enforcement implementation evidence recorded in Stage 8 implementation status.
- [x] AgentInstance lifecycle states are explicitly modeled and transition enforcement is implemented.
- [x] AgentInstance retirement is terminal and direct activation is blocked from the generic lifecycle path.
- [x] AgentInstance lifecycle API records actor/requester attribution in `agent_instance.lifecycle_changed` audit events.
- [x] Agent identity is first-class and tenant-scoped; independent access-review enforcement exists.

## Governance boundary audit

### Lifecycle

- [x] Lifecycle transition enforcement exists and has validation coverage.
- [x] Agent governance foundation migrations and API surfaces are present.
- [x] Full AgentInstance lifecycle evidence mapped to exact implementation files.
- [x] Retirement governance evidence completed for the current lifecycle model: retirement is terminal and disables execution.
- [ ] Replacement governance evidence completed. Replacement remains a certification gap until a distinct governed replacement workflow is implemented and tested.

### Identity and authorization

- [ ] Every protected agent action has explicit principal identity evidence.
- [x] Authorization decision records are mapped to execution trace metadata by the policy audit bridge.
- [ ] Agent-to-agent trust boundary acceptance tests completed.

### Tool governance

- [ ] Tool allow-list enforcement evidence collected.
- [ ] Side-effecting actions require policy evaluation.
- [ ] High-risk tool actions have approval binding.

### Auditability

- [ ] Every execution path has correlation and actor attribution evidence.
- [ ] Audit records are append-oriented and protected from ordinary mutation.

### Economics and safety

- [ ] Usage attribution mapped to tenant/agent/work item.
- [ ] Budget enforcement acceptance tests completed.
- [ ] Runaway execution protection evidence completed.

## AgentInstance lifecycle evidence mapping

| Requirement | Implementation evidence | Validation evidence | Status |
|---|---|---|---|
| Explicit lifecycle states | `backend/app/models/agent_instance.py` → `AgentInstanceStatus` | `backend/tests/test_agent_instance_lifecycle_governance.py` | Verified |
| Fail-closed transitions | `backend/app/services/agent_template_service.py` → `_ALLOWED_LIFECYCLE_TRANSITIONS` | `backend/tests/test_agent_instance_lifecycle_governance.py` | Verified |
| Governed mutation | `backend/app/services/agent_template_service.py` → `transition_instance` | `backend/tests/services/test_agent_template_service.py` | Verified |
| Direct activation blocked | `transition_instance` rejects `ENABLED` | `backend/tests/services/test_agent_template_service.py` | Verified |
| Lifecycle audit attribution | `backend/app/api/v1/agent_templates.py` → `agent_instance.lifecycle_changed` | API contract/source evidence | Verified |
| First-class identity | `backend/app/models/agent_identity.py` | `backend/tests/test_agent_governance_enforcement.py` | Verified |
| Independent access review | `backend/app/services/agent_governance.py` → `review_access` | `backend/tests/test_agent_governance_enforcement.py` | Verified |
| Terminal retirement | `RETIRED` has no outgoing transitions; execution disabled | `backend/tests/test_agent_instance_lifecycle_governance.py` | Verified |
| Replacement workflow | No distinct replacement operation currently exists | No acceptance test | Open gap |

## Reconciliation result

Implemented foundation areas must not be reported as fully certified capabilities until code, automated validation and operational evidence are linked together.

Current state:

- Workflow state governance: implementation validated.
- Test Center foundation: implementation validated.
- Agent governance foundation: implementation present, lifecycle evidence mapped, certification evidence pending.

## Next engineering sequence

1. Complete principal identity evidence for every protected agent action.
2. Audit existing tool governance and approval-binding paths against the governance checklist.
3. Define and implement a distinct governed replacement workflow before claiming replacement governance.
4. Add missing acceptance tests only where a real enforcement gap exists.
5. Update implementation evidence with exact commit SHAs.
6. Keep production claims blocked until deployment evidence exists.
