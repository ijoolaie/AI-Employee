# Tenant Workforce SLA Contract

## Status

Post-v1.4.11 engineering. This slice does not change the certified release identity and does not claim external production execution.

## Contract

Each tenant may own one workforce SLA contract with:

- max_queue_age_seconds
- enabled/disabled state
- effective timestamp
- creating/updating user identity
- tenant-scoped persistence

The contract is created or updated through the governed workforce API and requires the existing agent_workforce.ceo_approve permission. Read access uses agent_workforce.read.

## Dashboard semantics

When no active contract exists, the dashboard reports SLA tracking as unavailable and does not invent a target.

When an active contract exists, the dashboard reports:

- configured queue-age target;
- current active-queue compliance rate, calculated point-in-time from active WorkItem age;
- whether the oldest active WorkItem currently breaches the target.

This is explicitly NOT a historical completion-time SLA metric because WorkItem currently has no completion timestamp contract suitable for reconstructing historical SLA duration.

## Governance boundary

The SLA contract changes reporting only. It does not:

- reprioritize work;
- auto-reassign agents;
- provision or activate Agents;
- grant Manager authority;
- bypass approval, RBAC, access review, kill-switch or tenant isolation controls.

Future work may add a durable completion-time/SLA event model if historical SLA attainment is required.

## Release boundary

This implementation is post-v1.4.11 engineering and remains outside the immutable v1.4.11 certified snapshot.
