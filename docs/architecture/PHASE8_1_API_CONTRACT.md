# Phase 8.1 API Contract

## Principles

The API exposes WorkItem semantics, not separate Human-vs-Agent business APIs.

## Resource groups

### Work Items

- `POST /api/v1/work-items`
- `GET /api/v1/work-items`
- `GET /api/v1/work-items/{work_item_id}`
- `PATCH /api/v1/work-items/{work_item_id}`
- `POST /api/v1/work-items/{work_item_id}/assign`
- `POST /api/v1/work-items/{work_item_id}/execute`
- `POST /api/v1/work-items/{work_item_id}/cancel`

### Agents

- `GET /api/v1/agents`
- `POST /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `PATCH /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/{agent_id}/enable`
- `POST /api/v1/agents/{agent_id}/disable`

### Delegation

- `POST /api/v1/work-items/{work_item_id}/delegate`
- `POST /api/v1/work-items/{work_item_id}/handoff`

These endpoint names are a design contract for Phase 8 implementation; they are not claimed to exist on main yet.

## Executor payload

Executor references are typed and explicit:

```text
executor_type: human | agent
executor_id: opaque identifier
```

The API must reject executor references outside the caller's tenant/policy scope.

## Idempotency

Create, assign, execute, delegate and handoff mutations require idempotency semantics. Repeated requests must not create duplicate business execution.

## Errors

Use stable machine-readable error codes for:

- forbidden
- tenant_not_found
- work_item_not_found
- invalid_transition
- approval_required
- executor_unavailable
- tool_not_allowed
- budget_exceeded
- idempotency_conflict

## Compatibility

Legacy Employee/Run endpoints remain available during migration. They should internally converge on the same policy and audit rules where safely possible.
