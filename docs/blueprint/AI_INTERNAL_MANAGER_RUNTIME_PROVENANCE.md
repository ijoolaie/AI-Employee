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

## Role and template selection boundary

Internal Manager workforce proposals are **not restricted to a four-role allowlist**.

The Manager may select any role already present in the first-party workforce role catalog, including AI Internal Manager, and may propose a new role that is not yet present in the catalog.

The four current specialized roles are also represented in the first-party workforce role template catalog:

- `ai_marketing_advertising_manager`
- `ai_graphic_designer`
- `ai_software_developer`
- `ai_trader`

A known role records its catalog-defined approval class. A new role is treated as human-approval-required by default and is stored as a proposal definition rather than becoming an active role or bypassing template evaluation.

A new-role proposal should include `workforce_role_code`, `workforce_role_name`, `workforce_role_name_fa` when applicable, and `workforce_role_purpose` so the Board/CEO can evaluate the requested role.

The role/template selection does not bypass:

- CEO delegation for the Manager's proposal operation;
- Board review;
- CEO approval;
- AgentTemplate evaluation/publish;
- provisioning;
- access review;
- activation.

## Audit provenance

The Manager proposal audit event remains bound to the Manager AgentInstance and delegation. The runtime Run identity is retained in proposal configuration as manager_runtime_run_id for correlation with execution evidence.

## Next

Connect Manager proposal generation to the concrete runtime tool/action path and add workload/KPI/SLA/capacity reporting.
