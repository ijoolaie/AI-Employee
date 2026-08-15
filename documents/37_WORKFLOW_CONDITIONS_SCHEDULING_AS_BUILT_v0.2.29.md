# Workflow Conditions & Scheduling — As-Built v0.2.29

## Delivered
- Condition steps with `exists`, `equals`, `not_equals`, `contains`, `gt`, `gte`, `lt`, `lte`, `in`.
- Context paths rooted at `$.input`, `$.steps` and workflow context.
- Conditional downstream steps using `condition_ref` and `condition_value`.
- Durable `workflow_schedules` persistence.
- Five-field dependency-free cron evaluator.
- IANA timezone validation and UTC persistence for next execution.
- Celery schedule tick every 30 seconds; deployment requires a Celery Beat process.
- Row locking with `FOR UPDATE SKIP LOCKED` to reduce duplicate schedule claims.

## Boundary
This release does not claim event/webhook triggers, parallel execution, loops, cancellation, compensation, or human approval as workflow step primitives.
