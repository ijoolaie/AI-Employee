# AS-BUILT CURRENT STATE — v0.3.0

## Phase 1 (cumulative, unchanged)
- Phase 1 Core/RBAC, Employee/Run execution, AI Gateway/provider path,
  Memory/RAG foundations, Tool Registry, Workflow Engine, Human Approval,
  schedules, event/webhook triggers, workflow versioning, and customer/
  admin/developer operational surfaces remain cumulative — see
  `23_AS_BUILT_CURRENT_STATE_v0.2.47.md` for the full Phase 1 baseline.
  Nothing in Phase 1 was removed or behaviorally changed by this release.

## Phase 2 additions (this release)
- Added the `analyze_dataset` Tool to the Tool Registry.
- Added `app/services/report_service.py`: CSV/Excel parsing, KPI
  computation, a simple linear-trend forecast, chart rendering, and
  PDF/Excel report generation.
- Added the System Employee `report-employee`, seeded via
  `scripts/seed_report_employee.py`.
- Added `GET /api/v1/files/{file_id}/download` (closes a Phase 1 gap: files
  could previously be uploaded/listed/deleted but never retrieved).
- Added a whitelisted `report_artifacts` carry-through from Tool result to
  `Run.output_data` in `app/services/run_service.py`.
- Added frontend file-picker Run form and report-artifact download UI for
  the Report Employee, and a download button on the Files page.
- Full detail: `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.

## Verification boundary
- Python compile/static checks: PASS for the v0.3.0 additions
  (`python3 -m compileall app scripts`).
- Backend test suite: 91 passed in this build environment (83 carried over
  from v0.2.47 + 8 new in `tests/test_report_service.py`); one pre-existing
  test (`test_tool_registry.py`) was updated to reflect the new Tool.
- Static Alembic head analysis: unchanged, exactly one head
  (`7a2b3c4d5e6f`) — this release added zero migrations.
- Real PostgreSQL/Redis/Celery/LM Studio E2E for the Report Employee run
  path: **user-reported VERIFIED on 2026-08-09** ("تست فاز 2 کامل و بدون
  مشکل روی محیط واقعی انجام شد"). Not independently reproduced inside this
  delivery tool's own build environment — see
  `RELEASE_VERIFICATION_v0.4.0.md` for how this is tracked in the manifest.
- Frontend production build: NOT VERIFIED in this environment (no
  `node_modules`); TypeScript source follows exactly the component/hook
  patterns already shipped and building in Phase 1's pages.

## Phase 2 exit alignment
Per `03_Roadmap_v1.1.docx` §5, Phase 2 closes when "کاربر واقعی می‌تواند
فایل آپلود کند، گزارش و داشبورد بگیرد و نتیجه را دانلود کند" (a real user
can upload a file, get a report/dashboard, and download the result) with an
acceptable Run success rate. As of the user-reported real-environment test
on 2026-08-09, **Phase 2 is CLOSED**: the path is implemented in code and
has been exercised end-to-end against a live stack without issues per the
user's report.
