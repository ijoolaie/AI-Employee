# Workflow State Machine Audit Matrix

Last reconciled: 2026-09-14

## Scope

This document tracks the reconciliation between implementation, tests, documentation and execution-boundary guarantees for workflow state-machine enforcement.

## Implementation baseline

The workflow transition contract is implemented in:

`backend/app/services/workflow_state_machine.py`

Current contract:

- workflow step states are explicit;
- invalid transitions fail closed;
- terminal states cannot transition further;
- execution paths should not silently bypass lifecycle rules.

## Evidence

| Area | Status | Evidence |
|---|---|---|
| Transition guard | Verified | `assert_step_transition` contract |
| Explicit state list | Verified | `STEP_STATES` |
| Terminal state protection | Verified | empty transition sets |
| Test suite | Verified | 759 passed |
| Documentation alignment | In progress | This matrix |

## Remaining reconciliation checks

- Review all execution-bearing workers for direct status mutation.
- Verify every privileged transition has audit evidence.
- Keep CI evidence separate from production certification evidence.
- Update architecture docs after code-level gaps are closed.

## Rules

No new workflow state should be introduced without:

1. transition definition;
2. negative tests;
3. documentation update;
4. migration/recovery impact review.
