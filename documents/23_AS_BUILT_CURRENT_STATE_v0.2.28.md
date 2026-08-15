# Current As-Built State — v0.2.28

Authoritative current implementation snapshot.

## Implemented vertical path

Tenant → Employee → versioned Employee Run → optional RAG/Memory → AI Gateway → provider execution.

New orchestration layer:

Workflow → immutable WorkflowVersion → manual WorkflowRun → ordered WorkflowStepRun records → Employee Runs → propagated Workflow context.

## Current Workflow scope

The v0.2.28 engine is intentionally linear and manual. It is a real durable execution foundation, not a claim that the complete Workflow Engine design has been delivered.

Implemented: versioning, manual trigger, Employee action, context mapping, retries, durable state, child Run linkage, audit, RBAC.

Pending: schedule, events, conditions, loops, wait/approval, timeout, compensation/replay, parallelism, cancellation and visual builder.
