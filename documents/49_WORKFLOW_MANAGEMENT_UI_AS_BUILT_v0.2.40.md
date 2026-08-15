# Workflow Management UI — As Built v0.2.40

## Scope

This release completes the first usable Workflow Management surface on top of the immutable Workflow Version model introduced in v0.2.38 and the Visual Workflow Builder introduced in v0.2.39.

## Backend

- Added `GET /api/v1/workflows/{workflow_id}/runs`.
- Results are tenant-scoped, newest-first, and capped at 100 runs.
- Existing endpoints are consumed directly by the UI for:
  - version listing;
  - version activation;
  - run creation;
  - run inspection;
  - cancellation;
  - replay;
  - observability.

## Frontend

Workflow detail now provides:

- current workflow version;
- immutable version history;
- activation of historical versions;
- run history;
- explicit Workflow Version per run;
- live run status refresh;
- run selection;
- replay;
- cancellation;
- observability payload.

The Visual Builder remains the creation/editing surface. Saving creates a new immutable Workflow Version rather than mutating an existing version.

## Correctness

A selected run is always displayed against its stored `workflow_version_id`. Replay uses the backend replay contract and therefore does not silently move the replay to the current workflow version.

## Verification

- Backend Python compilation: PASS.
- Frontend dependency installation/build: NOT VERIFIED in the current environment because `frontend/node_modules` is unavailable.
- Generated TypeScript compiler state is excluded from the release package.
- Full E2E: remains NOT VERIFIED until PostgreSQL, Redis, Celery, and the frontend runtime are available.
