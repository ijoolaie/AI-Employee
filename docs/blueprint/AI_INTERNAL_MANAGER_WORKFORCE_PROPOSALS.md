# AI Internal Manager Workforce Proposal Integration

## Status

Post-v1.4.11 engineering work. This slice does not modify the certified `v1.4.11` tag and does not claim a new release.

## Governance boundary

The Internal Manager can originate a workforce proposal only when an active CEO delegation explicitly authorizes the requested operation.

Supported delegated proposal operations:

- `staffing_proposal`
- `replacement_proposal`
- `transfer_proposal`
- `retirement_proposal`

The proposal records:

- tenant
- Manager `AgentInstance`
- delegation record
- delegating CEO/user
- manager operation
- source type (`internal_manager`)
- sponsor
- requested workforce details
- rationale and configuration
- risk tier

The proposal still enters the existing governed lifecycle:

`Manager → Workforce Proposal → Board Review → CEO Approval → Provision → Access Review → Activation`

The Manager does **not** receive:

- direct provisioning authority
- direct retirement authority
- direct transfer execution authority
- financial commitment authority
- security-sensitive authority
- legal commitment authority
- production-critical authority
- irreversible execution authority

For transfer and retirement, this slice records the Manager's governed proposal intent and target identity; execution remains subject to the existing human-controlled workforce lifecycle and any operation-specific execution contract.

## Attribution

Human-originated proposals remain `source_type=human`.

Manager-originated proposals use:

- `source_type=internal_manager`
- `proposed_by_agent_instance_id`
- `delegation_id`
- `manager_operation`

The audit event `agent_workforce.proposal.manager_submitted` records the Manager, delegation, sponsor, operation, and target.

## Fail-closed behavior

A Manager proposal is rejected unless:

1. the Manager instance belongs to the same tenant;
2. the instance is the enabled `ai-internal-manager` role;
3. the delegation is active within its start/expiry window;
4. the delegation explicitly contains the requested operation;
5. an affected employee restriction, when present, includes the target;
6. the existing workforce proposal validation succeeds.

No delegation means no Manager-originated proposal.

## Next engineering slice

Connect Manager-originated proposals to the existing runtime/agent execution path so that the Manager identity is supplied by the governed agent runtime rather than a general-purpose user API call, while retaining the same delegation assertion and approval boundaries. Then add role-specific proposal validation and workload/KPI/SLA reporting.