# AS-BUILT CURRENT STATE — v0.5.0

## Governance note (read first)
Per `documents/61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, Phase 4's commercial
exit gate (real MRR + minimum paid subscribers) was **not** met before
this Phase 5 work started. Phase 5 was implemented at the user's explicit
direction, ahead of that gate. See
`documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md` for the full
note. This is a recorded fact, not a claim that the Roadmap's own
recommended sequencing was followed.

## Phase 1 (cumulative, unchanged)
See `23_AS_BUILT_CURRENT_STATE_v0.2.47.md` for the full Phase 1 baseline.

## Phase 2 (cumulative) — CLOSED
Report Employee. See `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`.
Closed per user-reported real-environment test, 2026-08-09.

## Phase 3 (cumulative) — tooling shipped, phase itself not claimed complete
Validation feedback/dashboard tooling. See
`59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md`.

## Phase 4 (cumulative) — implementation gate substantially implemented, commercial gate NOT proven
Billing plans/subscriptions/entitlements/MRR reporting. See
`62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md` and
`61_PHASE4_BASELINE_AUDIT_v0.4.1.md` for the explicit "not yet proven"
commercial-exit-gate status.

## Phase 5 additions (this release) — Document Employee
- Added the `analyze_document` Tool to the Tool Registry.
- Added `app/services/document_service.py`: PDF/image/DOCX/TXT text
  extraction (native text layer + Tesseract OCR fallback, English +
  Persian), regex-based field detection (dates, amounts, emails, phone
  numbers, ID-number candidates), and keyword-based document-type
  classification (contract/letter/form/administrative_document).
- Added the System Employee `document-employee`, seeded via
  `scripts/seed_document_employee.py`.
- Added a whitelisted `document_artifacts` carry-through from Tool result
  to `Run.output_data`, alongside the existing `report_artifacts` path.
- Added frontend file-picker Run form support and extracted-text download
  UI for the Document Employee.
- Full detail: `63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`.

## Verification boundary
- Python compile/static checks: PASS for the v0.5.0 additions.
- Backend test suite: **113 passed** in this build environment (103
  carried over from the uploaded v0.4.2 package + 10 new in
  `tests/test_document_service.py`). Two pre-existing tests were updated:
  `test_tool_registry.py` (new Tool) and `test_v036_e2e_contract.py`
  (this one had already drifted in the uploaded v0.4.2 package — it still
  asserted the Phase 3 head instead of the Phase 4 billing head; both that
  pre-existing gap and the new Phase 5 head were fixed together).
- Static Alembic head analysis: unchanged, exactly one head
  (`0a1b2c3d4e5f`) — this release added zero migrations.
- OCR/PDF extraction pipeline: actually exercised in this build
  environment against synthetic native-text and OCR-required inputs (not
  merely claimed) — see the Phase 5 As-Built for specifics. Real
  PostgreSQL/Redis/Celery/LM Studio E2E for the Document Employee Run
  path: **NOT VERIFIED** — no live services in this delivery environment,
  and (unlike Phase 2) no user report yet either, since this is new.
- Frontend: modified files syntax-checked with `esbuild` (parse-only);
  `next build` not run (no `node_modules` in this environment).

## Where the project stands against the Roadmap
- Phase 0 (Foundation): documented/agreed.
- Phase 1 (Core): CLOSED.
- Phase 2 (Report Employee): CLOSED (user-reported, 2026-08-09).
- Phase 3 (Validation): tooling shipped; the phase itself (3–5 real active
  customers with recorded feedback) has not been independently confirmed
  complete in these documents.
- Phase 4 (Monetization): implementation gate substantially implemented;
  commercial exit gate (positive/growing MRR + minimum paid subscribers)
  explicitly **not yet proven** per the project's own audit trail.
- Phase 5 (Document Employee): code-level IMPLEMENTED this release, at
  explicit user direction, ahead of the Phase 4 commercial gate being
  closed. Not yet exercised against a live stack or real documents/users.
- Phases 6–8 (Invoice/Order/Sales Employee): unchanged, still future work.
