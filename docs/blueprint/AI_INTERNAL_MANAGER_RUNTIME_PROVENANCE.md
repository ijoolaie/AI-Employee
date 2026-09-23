# AI Internal Manager Runtime Provenance

## Status

Post-v1.4.11 engineering. PR #643 established durable CEO delegation and proposal provenance. This slice closes the next boundary: Manager proposal submission is now available through the existing governed Agent runtime context rather than a general-purpose user API payload.

## Runtime identity boundary

Manager-originated proposal creation requires:

1. an active governed_agent_execution context;
2. the runtime tenant to match the proposal tenant;
3. a durable Run identity;
4. the bound AgentInstance to pass the existing Manager/delegation checks.

The Manager AgentInstance is therefore derived from the runtime context, not supplied by an API caller.

The public /agent-workforce/proposals/manager endpoint is intentionally removed. Human users continue to use the existing /agent-workforce/proposals endpoint for human-originated proposals.

## Governance

The runtime path still calls the existing CEO-delegation assertion. Runtime identity does not bypass:

- CEO delegation scope;
- affected-employee restrictions;
- Board review;
- CEO approval;
- provisioning;
- access review;
- activation.

No active workforce role is created by this slice.

## Audit provenance

The existing Manager proposal audit event remains bound to the Manager AgentInstance and delegation. The runtime Run identity is retained in proposal configuration as manager_runtime_run_id for correlation with execution evidence.

## Next

Add role-specific proposal validation for Marketing Manager, Graphic Designer, Software Developer and Trader, then connect Manager proposal generation to the concrete runtime tool/action path and add workload/KPI/SLA/capacity reporting.
