# As-Built Current State v0.2.19

## Implemented

- All v0.2.18 capabilities.
- Tool policy metadata: required permission and approval requirement.
- Worker-side re-authorization of tool calls using the Run creator's tenant-scoped RBAC roles.
- Fail-closed behavior for missing tool permissions.
- Explicit blocking of approval-required tools until Human Approval is implemented.
- Tool policy metadata exposed through the available-tools API.

## Current safe tools

- `calculator`: requires `run.execute`; no approval; no side effects.
- `current_time`: requires `run.execute`; no approval; no side effects.

## Security invariant

A model tool call is never sufficient authorization by itself. The tool must be registered, allowed by the immutable EmployeeVersion, pass JSON Schema validation, satisfy the tool permission policy in the worker, and satisfy approval policy.

## Still pending

- External tools.
- Side-effecting tools.
- Human Approval workflow.
- Durable dedicated ToolCall database spans.
- Tool-specific billing.
- RAG, Memory, Workflow, Quotas and Billing.
