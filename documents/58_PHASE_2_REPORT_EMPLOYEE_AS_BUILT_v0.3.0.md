# PHASE 2 — REPORT EMPLOYEE — AS-BUILT — v0.3.0

## Status of this document
As-Built (describes what was actually implemented in this package), not a
plan. Follows the verification rule from
`documents/45_PHASE_1_SCOPE_LOCK_v0.2.34.md`: a feature is IMPLEMENTED,
VERIFIED, PARTIAL, or DEFERRED — never assumed complete because a document
or placeholder exists.

## Scope
Per `03_Roadmap_v1.1.docx` §5 ("فاز دوم — Report Employee"):
> هدف: اولین Employee قابل استفاده و منبع اولین درآمد. ورودی: Excel/CSV.
> خروجی: Dashboard/Charts/KPIs/Insights/PDF/Excel. قابلیت‌ها: تحلیل داده،
> نمودار، گزارش مدیریتی، KPI، پیش‌بینی ساده، تحلیل متن، خلاصه‌سازی.
> معیار اتمام فاز: کاربر واقعی می‌تواند فایل آپلود کند، گزارش و داشبورد
> بگیرد و نتیجه را دانلود کند.

This release implements the Report Employee **inside the existing Phase 1
Core** (Employee → EmployeeVersion → Run → Tool Registry), per the
Roadmap's "Core First" principle — no parallel execution subsystem was
introduced.

## What was implemented

### 1. `analyze_dataset` Tool (`app/ai/tool_registry.py`)
A new controlled Tool, registered exactly like the existing `send_email`
Tool: JSON-Schema-validated input (`file_id`, UUID), `run.execute`
permission, `requires_approval=False` (read of an already tenant-owned
file + write of derived report files — no external side effects, no PII
leaves the tenant boundary). Execution is special-cased in
`ToolRegistry.execute()` to receive `db`/`tenant_id` from the active Run's
`TenantContext`, exactly as `send_email` does — `tenant_id` is **never**
accepted as a Tool argument from the model.

### 2. Report analysis engine (`app/services/report_service.py`)
Pure/deterministic core, independent of the AI Gateway, so KPI numbers in
the final report can never be an LLM hallucination:
- `_read_dataframe` — parses CSV or Excel (pandas), bounded to 200,000 rows.
- `_compute_kpis` — row/column counts, per-numeric-column sum/mean/min/max/
  missing (first 10 columns), per-categorical-column top-5 value counts
  (first 5 columns) — covers Roadmap "تحلیل داده" + "KPI".
- `_simple_forecast` — degree-1 linear trend (`numpy.polyfit`) over the
  first date-like + numeric column pair found; returns `None` when no
  suitable pair exists. Deliberately minimal, matching Roadmap "پیش‌بینی
  ساده" (not a general time-series model).
- `_render_charts` — up to 3 line charts (one per numeric column) + 1 bar
  chart (first categorical column, summed by first numeric column),
  rendered headless via `matplotlib.use("Agg")` — covers "نمودار".
- `_render_pdf` — a management-style PDF (KPI table + forecast paragraph +
  embedded chart images) via `reportlab` — covers "گزارش مدیریتی" + PDF
  output.
- `_render_excel` — a workbook with a `Data` sheet (first 5,000 rows) and a
  `KPI Summary` sheet, via `pandas.ExcelWriter`/`openpyxl` — covers Excel
  output.
- `analyze_dataset()` — orchestrates the above, then persists the PDF,
  Excel, and each chart PNG as ordinary tenant-scoped `FileObject` rows
  through the **existing** `file_service.upload_file()` / Object Storage
  path (`app/services/storage.py`) — no new storage backend, no new
  tenant-isolation surface. Records one `report.generated` audit event.

Text summarization/insight narration ("تحلیل متن", "خلاصه‌سازی") is
deliberately left to the calling model via the Employee prompt (see §3),
grounded in the tool's numeric output — this keeps the deterministic KPI
substrate auditable and separates it from any one AI provider's behavior.

### 3. Report Employee seed (`backend/scripts/seed_report_employee.py`)
An idempotent operator script (same convention as
`scripts/promote_platform_admin.py`) that creates the System Employee
`report-employee` (`tenant_id=NULL`, `kind="system"`) with:
- `input_schema`: `{file_id: uuid}` only.
- `allowed_tools`: `["analyze_dataset"]`.
- A prompt template instructing the model to call the tool once, narrate
  KPIs/insights/recommendations in the input's language grounded only in
  tool output, then emit a literal `PDF: <id>` / `Excel: <id>` footer.
- `output_schema` accepting the standard `{text}` shape plus an optional
  `report_artifacts` object (see §4).

Must be run once per environment after migrating; not baked into a
migration because it seeds application data into tables that already
exist, matching how `promote_platform_admin.py` is operated.

### 4. Structured report-artifact carry-through (`app/services/run_service.py`)
Small, additive change: the Run execution loop now tracks the last
successfully executed Tool's dict result (`last_tool_result`) in both the
resume-from-approval branch and the main tool-call loop. After the model's
final turn, if that result contains a `report_artifacts` dict, it is
merged onto `Run.output_data` alongside the existing `{"text": ...}` shape.
This is a whitelist merge of one specific key — it does not change the
model-facing message protocol, does not affect any other Employee's
output, and required no change to `validate_json_data` beyond the Report
Employee's own `output_schema` (which explicitly allows the extra key).

### 5. File download endpoint (`app/api/v1/files.py`)
`GET /api/v1/files/{file_id}/download` — tenant-scoped through the
existing `file_service.get_file()` + `FileReadContext` (permission
`file.read`), streams bytes from the existing Object Storage backend.
**This closes a real Phase 1 gap**: the Files API previously had no way to
retrieve a file's content at all (upload/list/get-metadata/delete only),
which meant the Roadmap's Phase 2 exit criterion "نتیجه را دانلود کند"
could not be met without it. Filed here because it is a direct
prerequisite for the Report Employee, not a separate Phase.

### 6. Frontend (`frontend/`)
- `lib/api.ts`: `downloadFile(id, filename)` — streams through the
  authenticated Axios client (a plain `<a href>` can't carry the Bearer
  token) and triggers a browser save via an object URL.
- `app/(customer)/files/page.tsx`: download button per row.
- `app/(customer)/employees/[id]/page.tsx`: when the Employee's slug is
  `report-employee`, the generic JSON-textarea Run form is replaced with a
  file `<select>` populated from `listFiles()`, so a real user can pick an
  uploaded CSV/Excel without hand-writing JSON.
- `app/(customer)/runs/[id]/page.tsx`: a "Report Employee — downloads"
  card renders when `run.output_data.report_artifacts` is present, with a
  PDF / Excel / per-chart download button each calling `downloadFile()`.
  Purely additive — invisible for every other Employee's Run.

No new frontend route was added; the existing generic Employee/Run pages
absorb the Report Employee per "Core First" (avoid building bespoke UI
ahead of a second specialized Employee needing it).

### 7. Dependencies
Added to `backend/requirements.txt` and `backend/pyproject.toml`:
`pandas`, `numpy`, `matplotlib`, `openpyxl`, `reportlab`.

## Explicitly NOT implemented in this release (deferred)
- **Automated report scheduling** (e.g. "run this report every Monday") —
  the existing Workflow Schedule engine (Phase 1) could drive this in a
  follow-up; not built here to keep this release's surface reviewable.
- **In-app chart/dashboard rendering** — charts are delivered as
  downloadable PNGs inside the PDF and as standalone files; an interactive
  in-browser dashboard view is DEFERRED.
- **Multi-file / multi-sheet analysis** in one Run — `analyze_dataset`
  takes exactly one `file_id` and (for Excel) reads the first sheet.
- **AI-driven column semantics** (e.g. auto-detecting "this looks like a
  sales table") — KPI/forecast selection is deterministic column-type
  based, not model-inferred.

## Verification boundary
- Python source compilation: PASS (`python3 -m compileall app scripts`).
- Backend unit test suite: **91 passed** (83 pre-existing + 8 new in
  `tests/test_report_service.py`), run locally with `asyncpg`,
  `python-jose`, `prometheus-client`, `pandas`, `matplotlib`, `openpyxl`,
  `reportlab` installed. This exceeds the "83 passed" baseline noted in
  `documents/23_AS_BUILT_CURRENT_STATE_v0.2.47.md` because the previously
  environment-blocked dependencies were available in this build
  environment — treat 91 as this build's number, not a claim about the
  user's own machine until they reproduce it there.
- `tests/test_tool_registry.py::test_registry_contains_controlled_initial_tools`
  was updated (not just left passing by luck) to assert the new
  `analyze_dataset` entry — flagged here explicitly per the project's own
  convention of never silently absorbing a test change into an unrelated
  diff.
- Static Alembic head analysis: unchanged — still exactly one head,
  `7a2b3c4d5e6f`. No migration was added; this release introduces zero new
  tables (report artifacts reuse the existing `files` table).
- `analyze_dataset()`'s DB/Object-Storage-backed path (as opposed to the
  pure functions above) has **NOT** been exercised against a real
  PostgreSQL/Redis/LM Studio stack in this delivery environment — this
  package build has no live services, exactly the same boundary already
  documented for v0.2.28 through v0.2.47. Run `scripts/seed_report_employee.py`
  and a real Run against a live model before relying on this in
  production.
- Frontend: TypeScript source was hand-reviewed against existing working
  patterns (`Button`, `Card`, `useQuery`/`useMutation`, `api.ts` Axios
  instance) already exercised by Phase 1's shipped pages; `next build`
  was **not** run in this environment (no `node_modules`) — same
  documented boundary as every prior frontend change in this project.

## Package/version bump
- `backend/pyproject.toml`: `0.2.47` → `0.3.0`.
- `frontend/package.json`: `0.2.47` → `0.3.0`.
- `app/main.py` FastAPI `version=` bumped to `0.3.0` to match.

## v0.4.0 update — real-environment verification (user-reported)
The user reported, outside this build environment, that Phase 2 was
**"تست فاز 2 کامل و بدون مشکل روی محیط واقعی انجام شد"** (Phase 2 testing
completed fully and without issues on a real environment) as of 2026-08-09.
This is recorded here as a **user-reported** verification, not one
independently reproduced by this delivery tool — this package build still
has no live PostgreSQL/Redis/LM Studio stack to verify against itself.
Per the project's own verification-status convention, `real_postgresql_
redis_celery_e2e` in `PROJECT_FILE_MANIFEST.json` is updated to
`VERIFIED_USER_REPORTED_2026-08-09` rather than a bare `PASS`, so the
source of the claim stays traceable. Phase 2 is now considered **CLOSED**
per `03_Roadmap_v1.1.docx` §5's Definition of Done.
