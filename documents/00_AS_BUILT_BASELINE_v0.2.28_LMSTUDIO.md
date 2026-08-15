# As-Built Baseline v0.2.28 — LM Studio

This is the authoritative cumulative implementation baseline for v0.2.28. All prior implemented changes remain in scope unless explicitly superseded.

## Current runtime

Employee Run: validation → optional RAG → optional Employee Memory → Prompt + Context Assembly → Tool/Approval boundary → AI Gateway → provider registry → LM Studio / Anthropic.

Workflow Run now sits above Employee Run as an orchestration layer:

`WorkflowVersion → ordered Employee Action steps → child Employee Runs → shared Workflow context → durable Workflow trace/state`.

## Current implemented domains

- Multi-tenant RBAC and tenant isolation
- Employee + immutable EmployeeVersion
- Async Employee Run via Celery
- AI Gateway and LM Studio
- JSON Schema validation foundation/hardening
- RAG and tenant-scoped retrieval
- Employee Memory, automatic extraction and lifecycle/versioning
- Tool registry and approval boundary
- Durable SMTP outbox
- Usage/cost reporting
- Workflow Engine foundation

## Workflow Engine v0.2.28

Implemented: tenant-scoped workflows, versioned definitions, manual trigger, linear Employee Action steps, context mapping, step retry count, durable WorkflowRun/WorkflowStepRun state, child Employee Run linkage, audit and workflow RBAC.

Not yet implemented: Schedule/Event triggers, Condition/Loop/Wait as generalized steps, timeout enforcement, compensation/replay, parallelism, cancellation and visual builder.

## Verification status

Source compilation and focused workflow static tests pass. Full integration pytest is environment-dependent and must be run in an environment containing all backend runtime dependencies.

This distinction is part of the release truth and must not be replaced by a blanket PASS.
