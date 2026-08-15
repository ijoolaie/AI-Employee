# AI Employee Platform — v0.5.0 Package Verification (Phase 5: Document Employee)

This package adds Phase 5 (Document Employee) on top of the uploaded
v0.4.2 package (Phase 4 Monetization). It contains:
- `backend/`
- `frontend/`
- `documents/`
- `DEV_SETUP.md`
- `CHANGELOG.md`
- `PROJECT_FILE_MANIFEST.json`

## Governance note
`documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md` recorded that Phase 4's
commercial exit gate (real MRR + minimum paid subscribers) was not met,
and recommended holding Phase 5 until it was. This release proceeds with
Phase 5 at the user's **explicit direction**, ahead of that gate. See
`documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md` for the full
note — this verification document does not repeat it beyond this flag.

## Migration verification
No new Alembic migration was added in this release. Static Alembic
revision analysis reports exactly one head, unchanged from the uploaded
v0.4.2 package:

`0a1b2c3d4e5f`

Extracted document text is persisted as ordinary rows in the existing
`files` table via the existing `file_service.upload_file()` path — no
schema change was required or made.

## Source verification
- Python source compilation: PASS (`python3 -m compileall app scripts`
  across `backend/`).
- Static Alembic head analysis: PASS — exactly one head (`0a1b2c3d4e5f`),
  unchanged from the uploaded package.
- Backend unit test suite: **113 passed** in this build environment (103
  from the uploaded v0.4.2 package + 10 new in
  `tests/test_document_service.py`). Two pre-existing tests were updated:
  `tests/test_tool_registry.py` (new `analyze_document` Tool) and
  `tests/test_v036_e2e_contract.py` — the latter had a **pre-existing gap
  in the uploaded package**: it still asserted the Phase 3 Alembic head
  (`b3c4d5e6f713`) instead of the Phase 4 billing head (`0a1b2c3d4e5f`)
  that was already the actual head in the uploaded ZIP. Both that gap and
  the new Phase 5 head were corrected together.
- OCR/PDF pipeline: exercised against synthetic inputs in this build
  environment (a `reportlab`-generated native-text PDF, correctly routed
  to native extraction; a `Pillow`-generated PNG requiring OCR, correctly
  routed to Tesseract and producing readable text including a correctly
  recognized email address). `tesseract-ocr`, `tesseract-ocr-fas`, and
  `poppler-utils` were confirmed installed and functional in this
  environment.
- Full PostgreSQL/Redis/Celery/LM Studio E2E: **not claimed** — no live
  services available in this delivery environment, and (unlike Phase 2)
  no user report exists for this Phase yet either, since it is new in
  this release.
- Frontend: modified files (`employees/[id]/page.tsx`, `runs/[id]/
  page.tsx`) were syntax-checked with `esbuild` (TSX parse only — full
  type-checking requires `node_modules`, not installed in this
  environment). `next build` was not run.

## New surface in this release
- `analyze_document` Tool, callable only by the `document-employee`
  System Employee's Runs via the existing Tool Registry execution path.
- `report_artifacts` carry-through on `Run.output_data` (Phase 2) is now
  joined by an equivalent, separately-whitelisted `document_artifacts`
  carry-through — both additive, neither affects any other Employee.

## Required manual step before first use
`scripts/seed_document_employee.py` must be run once against the target
database to create the `document-employee` System Employee, exactly like
`scripts/seed_report_employee.py` was required for Phase 2. The
`tesseract-ocr`, `tesseract-ocr-fas`, and `poppler-utils` system packages
must also be installed on the host — see `DEV_SETUP.md`.

## Consistency fixes applied in this package
- `backend/pyproject.toml`, `frontend/package.json`,
  `backend/app/main.py` all aligned to `0.5.0` (were `0.4.2`).
- `CHANGELOG.md` and `backend/CHANGELOG.md` both updated with the v0.5.0
  entry.
- `tests/test_v036_e2e_contract.py`'s stale Alembic-head assertion (a gap
  present in the uploaded v0.4.2 package, predating this release) was
  corrected alongside the new Phase 5 addition.
- `PROJECT_FILE_MANIFEST.json` regenerated (paths, sizes, sha256 for every
  file in the package) and `verification_status` updated.

## Release note
This release adds the Document Employee (Phase 5) without modifying
Phase 1–4 behavior for any existing Employee, Workflow, Billing, or API
surface outside the additive changes listed above. It is explicitly
sequenced ahead of the Phase 4 commercial exit gate at the user's
direction — see the governance note above and in the Phase 5 As-Built
document. Documentation, changelogs, and the file manifest have been
synchronized with the actual code and test state as of this build.
