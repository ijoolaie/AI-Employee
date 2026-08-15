# Schedule UI — As Built — v0.2.42

## Scope

Phase 1 Schedule UI for durable workflow schedules.

## Implemented

- Tenant-scoped schedule catalog.
- Schedule creation against an active workflow.
- Five-field cron expression input.
- IANA timezone input and validation.
- Next-run and last-run visibility.
- Active/Paused status.
- Pause/resume action.
- Delete action with confirmation.
- Automatic refresh of the schedule catalog.
- Backend schedule update/delete endpoints.
- Audit events for schedule update and deletion.
- Existing durable scheduler/Beat remains the execution authority; UI only manages persisted schedule definitions.

## API

- `GET /api/v1/workflow-schedules`
- `POST /api/v1/workflows/{workflow_id}/schedules`
- `GET /api/v1/workflows/{workflow_id}/schedules`
- `PATCH /api/v1/workflow-schedules/{schedule_id}`
- `DELETE /api/v1/workflow-schedules/{schedule_id}`

All authenticated management operations remain tenant-scoped and require the existing `workflow.read` / `workflow.write` permissions.

## Execution Semantics

The UI does not execute schedules directly. The persisted `WorkflowSchedule` is still claimed by the Celery schedule tick worker. Updating an active schedule recomputes its next occurrence using the configured timezone. Pausing clears `next_run_at`; resuming computes a fresh next occurrence.

## Verification

- Python AST/compile checks: required.
- Migration graph: unchanged; no schema migration required for this UI/API hardening step.
- Full PostgreSQL/Redis/Celery E2E: not claimed unless external services are available.
- Frontend production build: not claimed when `node_modules` is unavailable.
