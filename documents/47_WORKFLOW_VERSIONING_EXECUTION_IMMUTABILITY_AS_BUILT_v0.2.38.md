# Phase 1 — Workflow Versioning & Execution Immutability — v0.2.38

## Scope
This release closes the Workflow Versioning/Execution Immutability gap in Phase 1. Workflow definitions are immutable after publication; changes create a new version. Each Workflow Run is pinned to one WorkflowVersion and carries a run-local execution contract containing the resolved immutable EmployeeVersion references used by its steps.

## Implemented
- `WorkflowVersion.execution_contract` stores the resolved execution contract.
- `WorkflowVersion.content_hash` provides deterministic SHA-256 integrity identity.
- Unique `(workflow_id, version_number)` constraint.
- Database partial unique index guarantees one current version per workflow.
- PostgreSQL trigger rejects definition mutation/deletion while allowing only current-version activation changes.
- New version creation and activation APIs.
- Manual Run creation may target a historical WorkflowVersion explicitly.
- Workflow execution reads the run-local execution contract and passes the pinned `EmployeeVersion` into child Runs.
- Replay creates a new Run pinned to the exact source WorkflowVersion and source execution contract.
- Replay metadata records source Run and source version.

## Compatibility
WorkflowVersion rows created before v0.2.38 are marked `legacy` in their execution contract. When such a version is first executed by a new Run, the current EmployeeVersion references are materialized into that Run's contract without mutating the historical WorkflowVersion. New versions are fully snapshotted at publication time.

## APIs
- `GET /api/v1/workflows/{workflow_id}/versions`
- `GET /api/v1/workflows/{workflow_id}/versions/{version_id}`
- `POST /api/v1/workflows/{workflow_id}/versions`
- `POST /api/v1/workflows/{workflow_id}/versions/{version_id}/activate`
- `POST /api/v1/workflows/{workflow_id}/runs` with optional `workflow_version_id`
- `POST /api/v1/workflows/{workflow_id}/runs/{run_id}/replay`

## Verification
Static Python compilation and targeted contract tests are required. Live PostgreSQL trigger behavior and full E2E remain environment-dependent until PostgreSQL/Redis/Celery are available.
