# Policy Decision Audit Evidence Bridge

## Status
Identified governance gap.

## Finding
The agent policy kernel produces deterministic `ALLOW`, `DENY`, and `REQUIRE_APPROVAL` decisions, but the decision itself is not yet persisted as an audit ledger event at the policy kernel boundary.

## Required change
Add a policy decision audit bridge so every authorization decision records:

- tenant_id
- agent_instance_id
- action
- tool_name
- run_id
- tool_call_id
- policy_version
- decision
- reason

## Acceptance criteria

- Every policy decision has immutable audit evidence.
- Denied and approval-required decisions are recorded.
- Existing authorization behavior remains fail-closed.
- Existing policy tests remain green.
