# AI Employee Platform — v0.3.0 Package Verification (Phase 2 start)

This package adds Phase 2 (Report Employee) on top of the complete Phase 1
release (`RELEASE_VERIFICATION_FIXED.md`, v0.2.47). It contains:
- `backend/`
- `frontend/`
- `documents/`
- `DEV_SETUP.md`
- `CHANGELOG.md`
- `PROJECT_FILE_MANIFEST.json`

## Migration verification
No new Alembic migration was added in this release. Static Alembic
revision analysis reports exactly one head, unchanged from v0.2.47:

`7a2b3c4d5e6f`

Report artifacts (PDF/Excel/chart PNGs) are persisted as ordinary rows in
the existing `files` table via the existing `file_service.upload_file()`
path — no schema change was required or made.

## Source verification
- Python source compilation: PASS (`python3 -m compileall app scripts`
  across `backend/`).
- Static Alembic head analysis: PASS — exactly one head (`7a2b3c4d5e6f`),
  unchanged from v0.2.47.
- Backend unit test suite: **91 passed** in this build environment (83
  pre-existing Phase 1 tests + 8 new in `tests/test_report_service.py`).
  `tests/test_tool_registry.py::test_registry_contains_controlled_initial_tools`
  was updated to include the new `analyze_dataset` Tool.
- Full PostgreSQL/Redis/Celery/LM Studio E2E: **not claimed** by this
  package build alone — no live services are available in this delivery
  environment, same boundary as every Phase 1 release since v0.2.28.
- Frontend build: requires Node.js dependencies to be installed; not run
  in this environment. TypeScript source follows existing shipped
  component/hook patterns (`Button`, `Card`, `useQuery`/`useMutation`,
  the `api.ts` Axios instance).

## New surface in this release
- `POST` (via the standard `POST /api/v1/runs` on `report-employee`) →
  `analyze_dataset` Tool → KPIs, chart PNGs, PDF report, Excel report.
- `GET /api/v1/files/{file_id}/download` — new; the Files API previously
  had no content-retrieval route.
- `report_artifacts` key, additive and whitelisted, on `Run.output_data`
  when the executing Employee's last Tool call returned that shape.

## Required manual step before first use
`scripts/seed_report_employee.py` must be run once against the target
database (`python scripts/seed_report_employee.py` from `backend/`, with
`DATABASE_URL` configured) to create the `report-employee` System
Employee. It is intentionally not baked into a migration, following the
same operational convention as `scripts/promote_platform_admin.py`.

## Consistency fixes applied in this package
- `backend/pyproject.toml` version aligned to `0.3.0` (was `0.2.47`).
- `frontend/package.json` version aligned to `0.3.0` (was `0.2.47`).
- `backend/app/main.py` FastAPI `version=` aligned to `0.3.0`.
- `CHANGELOG.md` and `backend/CHANGELOG.md` both updated with the v0.3.0
  entry (avoiding the kind of drift documented as fixed in
  `RELEASE_VERIFICATION_FIXED.md` for v0.2.47).
- `PROJECT_FILE_MANIFEST.json` updated with the new/changed files listed
  below.

## Release note
This release adds the Report Employee (Phase 2 start) without modifying
Phase 1 behavior for any existing Employee, Workflow, or API surface
outside the additive changes listed above. Documentation, changelogs, and
the file manifest have been synchronized with the actual code and test
state as of this build.
