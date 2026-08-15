# RC8 P0–P3 Implementation

Baseline: `AI_Employee_Platform_RC8_fixed_api_proxy_v2(1).zip`

## P0
- Added `RC8_IMPLEMENTATION_MATRIX.md`.
- Recorded the Docker/runtime verification already completed.
- Classified features as implemented/remaining instead of treating route existence as verification.

## P1
- Added tenant API key persistence and lifecycle.
- Added API key create/list/revoke endpoints under `/api/v1/api-keys`.
- API key secrets are SHA-256 digested; plaintext is returned only at creation.
- Added `X-API-Key` authentication support to the common tenant context.
- Corrected developer navigation route prefixes.
- Added Tasks, Reports and Logs to the primary sidebar.

## P2
- Added `/tasks` as a Run-backed operational task queue.
- Added `/reports` as a customer-facing KPI, reliability and cost report.
- Kept Chat wired to the existing real Run execution path.
- Kept existing Employees, Runs, Knowledge, Memory and Approvals surfaces.

## P3
- Added a dedicated `/logs` tenant-scoped audit/operational log view.
- Kept `/developer` as the Developer Console for runtime metrics and DLQ recovery.
- Kept `/traces` as the Trace Explorer for planner/memory/tool/LLM event inspection.
- API credentials are now usable through `X-API-Key`, while browser sessions continue using bearer JWTs.

## Validation
- Python source files introduced/changed were syntax-compiled successfully during implementation.
- Frontend contract test was extended for P0–P3 coverage.
- Full Next.js install/build could not be completed in the implementation environment because dependency installation exceeded the available execution window; run `npm install` and `npm run build` in the project environment before runtime certification.
- Database migration must be applied before exercising API-key CRUD:
  `alembic upgrade head`
