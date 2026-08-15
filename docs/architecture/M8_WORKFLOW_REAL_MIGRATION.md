# M8 — Workflow Real Migration

## First production-domain migration
Workflow is the first bounded context whose core execution use-case has moved
from architecture scaffolding into a real domain/application implementation.

### Migrated
- `WorkflowRun` domain model
- `WorkflowRunRepository` port
- `WorkflowExecutor` port
- `WorkflowApplicationService`
- success/failure state transitions
- `workflow.run.completed` domain event
- infrastructure adapters
- isolated unit tests

### Compatibility
The existing RC8 workflow engine is not deleted. It is wrapped by
`LegacyWorkflowExecutor`. Existing callers can migrate incrementally.

### Why Workflow first?
Workflow is a central orchestration boundary and a good test of the architecture:
it touches persistence, execution, events, and asynchronous behavior without
requiring a database schema migration in the first step.

## Next
M9 should migrate Knowledge/RAG, then CRM, Commerce, and Billing using the same
pattern.
