# Stage 8 Governance Audit Checklist

**Date:** 2026-09-14

## Purpose

This checklist tracks reconciliation between Stage 8 design requirements, repository implementation, tests and evidence.

## Current verified evidence

- [x] Repository validation completed: `759 passed`.
- [x] Workflow state-machine enforcement branch validated locally.
- [x] Test warning cleanup completed through pytest configuration reconciliation.
- [x] Engineering evidence is separated from production certification evidence.

## Governance boundary audit

### Lifecycle

- [x] Lifecycle transition enforcement exists and has validation coverage.
- [ ] Full AgentInstance lifecycle evidence mapped to exact implementation files.
- [ ] Retirement/replacement governance evidence completed.

### Identity and authorization

- [ ] Every protected agent action has explicit principal identity evidence.
- [ ] Authorization decision records mapped to audit events.
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

## Next engineering sequence

1. Map existing lifecycle/security code paths to Stage 8 requirements.
2. Add missing acceptance tests only where a real enforcement gap exists.
3. Update implementation evidence with exact commit SHAs.
4. Keep production claims blocked until deployment evidence exists.
