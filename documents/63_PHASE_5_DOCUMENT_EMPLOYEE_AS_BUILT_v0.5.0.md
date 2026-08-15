# PHASE 5 — DOCUMENT EMPLOYEE — AS-BUILT — v0.5.0

## Status of this document
As-Built (describes what was actually implemented), not a plan. Follows
the verification rule from `documents/45_PHASE_1_SCOPE_LOCK_v0.2.34.md`.

## A required governance note — read this first
`documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md` recorded an explicit
decision: **"Phase 4 is NOT complete"** and **"No Phase 5 implementation
should be started as a formal roadmap phase until these gates are met"**
(the roadmap gates being: real payment-provider integration, real paid
subscription transactions, and the roadmap-required paid-subscriber/MRR
evidence). `documents/62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md` confirms
the "commercial exit gate: not yet proven" status has not changed since.

**Phase 5 implementation in this release was started at the user's
explicit direction** ("فاز ۵ رو شروع کن"), not because the Phase 4
commercial gate was met. This document records that fact rather than
silently overriding the prior audit's recommendation. The decision to
sequence work ahead of the roadmap's own stated dependency order is the
project owner's to make — it is recorded here so a future reader (or a
future As-Built synchronization pass) does not mistake this for the gate
having been satisfied.

## Scope
Per `03_Roadmap_v1.1.docx` §8 ("فاز پنجم — Document Employee"):
> OCR · پردازش PDF · قرارداد · نامه · فرم · اسناد اداری

As with Phase 2 (Report Employee), this is implemented **inside the
existing Phase 1 Core** (Employee → EmployeeVersion → Run → Tool
Registry) — no parallel execution subsystem.

## What was implemented

### 1. `analyze_document` Tool (`app/ai/tool_registry.py`)
Registered exactly like `analyze_dataset`: JSON-Schema-validated input
(`file_id`, UUID), `run.execute` permission, `requires_approval=False`
(read of an already tenant-owned file + write of one derived text file —
no external side effects). Execution is special-cased in
`ToolRegistry.execute()` to receive `db`/`tenant_id` from the active Run's
`TenantContext`; `tenant_id` is never accepted as a Tool argument from the
model.

### 2. Document analysis engine (`app/services/document_service.py`)
Deterministic core, independent of the AI Gateway, for the same reason
`report_service.py` is: every fact in the final narration must trace back
to code, not to LLM inference.
- **Text extraction, four input types**: PDF (`pypdf` for the native text
  layer; falls back page-by-page to OCR via `pdf2image` + `pytesseract`
  when a page has fewer than `MIN_CHARS_PER_PAGE_FOR_NATIVE_TEXT` (20)
  characters of native text — this is what makes scanned contracts/forms
  work, not just born-digital PDFs), PNG/JPEG/WEBP/TIFF/BMP images (direct
  OCR), DOCX (`python-docx`), and TXT/MD (direct decode, multi-encoding
  fallback). Bounded to `MAX_PAGES = 50` per document.
- **OCR language**: `eng+fas` (English + Persian) — verified working in
  the build environment against both a synthetic English test image and
  a synthetic PDF, using the `tesseract-ocr` + `tesseract-ocr-fas` system
  packages and `poppler-utils` (for PDF→image rendering).
- **Field detection** (`_detect_fields`): regex-based, auditable — dates
  (Gregorian and Jalali-shaped `13xx`/`14xx` patterns), monetary amounts
  (with ریال/تومان/$/€/USD/IRR/EUR markers), email addresses, Iranian-style
  phone numbers, and 10–11 digit ID-number *candidates* (not
  checksum-validated — flagged as candidates deliberately, not asserted
  as valid national IDs).
- **Document-type classification** (`_classify_document_type`):
  keyword-vote heuristic mapping to the Roadmap's own four categories —
  `contract` / `letter` / `form` / `administrative_document` (default).
  Deliberately not a model call, same "deterministic substrate" principle
  as `report_service._simple_forecast`.
- **Persistence**: the full extracted text is saved as an ordinary
  tenant-scoped `FileObject` via the existing `file_service.upload_file()`
  path — no new storage backend, no new tenant-isolation surface. One
  `document.analyzed` audit event is recorded per Run.

Narration/summarization (what the document *means*, what actions it
implies) is left to the calling model via the Employee prompt, grounded
in this module's structured output — same separation of concerns as
Phase 2.

### 3. Document Employee seed (`backend/scripts/seed_document_employee.py`)
Idempotent, same convention as `scripts/seed_report_employee.py`. Creates
the System Employee `document-employee` (`tenant_id=NULL`,
`kind="system"`) with `input_schema: {file_id: uuid}`,
`allowed_tools: ["analyze_document"]`, a prompt template instructing the
model to call the tool once and narrate strictly from its output, and an
`output_schema` accepting `{text}` plus an optional `document_artifacts`
object.

### 4. Structured artifact carry-through (`app/services/run_service.py`)
The existing whitelist merge (added in Phase 2 for `report_artifacts`) was
extended, not replaced, to also recognize a `document_artifacts` dict on
the last executed Tool's result. Still a targeted, additive change — no
other Employee's output shape is affected, and the merge logic remains a
closed whitelist of two known keys, not an open pass-through.

### 5. Frontend (`frontend/`)
- `app/(customer)/employees/[id]/page.tsx`: the existing Report-Employee
  file-picker Run form was generalized (`usesFilePicker`) to also cover
  `document-employee`, with a type-appropriate label ("Document file (PDF,
  image, or DOCX)" vs. "Dataset file (CSV or Excel)").
- `app/(customer)/runs/[id]/page.tsx`: a "Document Employee — downloads"
  card renders when `run.output_data.document_artifacts.extracted_text_
  file_id` is present, with a download button using the existing
  `downloadFile()` helper — purely additive, invisible for every other
  Employee's Run.

No new frontend route was added, following the same "Core First" /
generic-page-first reasoning as Phase 2.

### 6. Dependencies
Added to `backend/requirements.txt` and `backend/pyproject.toml`:
`pytesseract`, `pdf2image`, `pillow`. These require the `tesseract-ocr`
(+ `tesseract-ocr-fas` for Persian) and `poppler-utils` **system**
packages — not installable via pip — documented in `DEV_SETUP.md`.

## Explicitly NOT implemented in this release (deferred)
- **Checksum validation of detected Iranian national ID/economic-code
  candidates** — flagged as candidates only; validating the actual
  checksum algorithm is a follow-up, not done here.
- **Structured contract-clause extraction** (e.g., automatically pulling
  out "termination clause", "payment terms" as separate structured
  fields) — the Roadmap lists "قرارداد" as an input category, not a
  clause-extraction requirement; the current classification + full-text
  narration meets the stated scope without over-building.
- **Form-field (checkbox/table) structured extraction** — forms are
  OCR'd and text-extracted like any other document; parsing checkbox
  states or table cell structure specifically is DEFERRED.
- **Multi-file batch processing** — `analyze_document` takes exactly one
  `file_id` per call, same single-file design as `analyze_dataset`.
- **Language auto-detection beyond OCR's own eng+fas pass** — no separate
  language-ID step; Tesseract is simply run with both language packs
  loaded simultaneously.

## Verification boundary
- Python source compilation: PASS (`python3 -m compileall app scripts`).
- **OCR/PDF pipeline actually exercised, not just claimed**: a synthetic
  PDF (via `reportlab`, native text layer) and a synthetic PNG (via
  `Pillow`, requiring OCR) were both run through
  `document_service._extract_text_from_pdf` /
  `_extract_text_from_image` in this build environment, and correctly
  routed to the `native` and `ocr` code paths respectively, with Tesseract
  producing readable output including a correctly-recognized email
  address. Persian OCR language data (`tesseract-ocr-fas`) was confirmed
  installed and loadable (`pytesseract.get_languages()` includes `fas`),
  though no Persian-script OCR accuracy benchmark was run.
- Backend unit test suite: **113 passed** in this build environment (103
  carried over from the uploaded v0.4.2 package + 10 new in
  `tests/test_document_service.py`).
- `tests/test_tool_registry.py::test_registry_contains_controlled_initial_tools`
  and `tests/test_v036_e2e_contract.py::test_migration_merge_has_single_revision`
  were both updated for real, intentional reasons flagged explicitly here:
  the former for the new `analyze_document` Tool, the latter because the
  **uploaded v0.4.2 package itself had not updated this assertion** for
  the Phase 4 billing migration head (`0a1b2c3d4e5f`) — that gap predates
  this release and was fixed as part of establishing a clean baseline
  before adding Phase 5 work.
- Static Alembic head analysis: **unchanged** at `0a1b2c3d4e5f` — Phase 5
  introduced zero new tables; extracted text reuses the existing `files`
  table exactly like Phase 2's report artifacts.
- `analyze_document()`'s DB/Object-Storage-backed path (as opposed to the
  pure extraction/detection functions above) has **NOT** been exercised
  against a real PostgreSQL/Redis/LM Studio stack in this delivery
  environment. Run `scripts/seed_document_employee.py` and a real Run
  against a live model before relying on this in production.
- Frontend: modified/added files were syntax-checked with `esbuild`
  (TSX/TS parse only, not full type-checking against `node_modules`,
  which was not installed in this environment) — all passed. `next
  build` was **not** run.

## Package/version bump
- `backend/pyproject.toml`: `0.4.2` → `0.5.0`.
- `frontend/package.json`: `0.4.2` → `0.5.0`.
- `app/main.py` FastAPI `version=` bumped to `0.5.0`.

## Recommended next steps (not part of this delivery)
1. Decide, as the project owner, whether to return to closing the Phase 4
   commercial exit gate (real payment provider, real MRR evidence) before
   further Phase 5+ work, given `61_PHASE4_BASELINE_AUDIT_v0.4.1.md`'s
   explicit recommendation.
2. Run `pip install -r requirements.txt` (now including the OCR
   dependencies) and confirm `tesseract-ocr` / `tesseract-ocr-fas` /
   `poppler-utils` are installed in the deployment environment — this
   Phase does not work without those system packages present.
3. Run `python scripts/seed_document_employee.py` once per environment.
4. Exercise the Document Employee against a real scanned contract/letter/
   form and confirm OCR quality is acceptable before relying on it with
   real customers.
