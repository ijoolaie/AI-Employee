# Phase 7 Scope Lock — Invoice Employee (targeting v0.7.0)

## Purpose
This document resolves the phase-numbering ambiguity flagged in
`23_AS_BUILT_CURRENT_STATE_v0.6.0.md` ("A numbering note") and locks
scope before implementation starts, following the same pattern as
`45_PHASE_1_SCOPE_LOCK_v0.2.34.md`.

## Numbering resolution
`03_Roadmap_v1.1.docx` §8 originally labeled "فاز ششم" (Phase 6) as
Invoice Employee. `v0.6.0` used the "Phase 6" label instead for the
Stripe payment-provider adapter (closing the Phase 4 implementation
gap), per the project owner's explicit choice at the time. **This
document formally renumbers the Roadmap's Employee sequence by one:**

| Roadmap §8 label | Actual project phase |
|---|---|
| فاز پنجم — Document Employee | Phase 5 (shipped, `v0.5.0`) |
| فاز ششم — Invoice Employee | **Phase 7** (this document, targeting `v0.7.0`) |
| فاز هفتم — Order Employee | Phase 8 |
| فاز هشتم — Sales Employee | Phase 9 |

(The Stripe adapter keeps its existing "Phase 6" label in
`64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md` — that document is not
renamed, since as-built documents for shipped releases are not rewritten
after the fact. Only the forward-looking Employee sequence is
renumbered.)

## Governance status
Per `61_PHASE4_BASELINE_AUDIT_v0.4.1.md`, the Phase 4 **commercial** exit
gate (proven MRR + minimum paid subscribers) is still open — `v0.6.0`
closed only the implementation half. The project owner has now directed
the project to proceed to Phase 7 (Invoice Employee) rather than pause
for the commercial gate, consistent with the same choice already made
before Phase 5. This is noted here, not silently omitted, exactly as
prior phase-sequencing decisions have been recorded in this project.

## Phase 7 mandatory scope (from Roadmap §8: "صدور، تحلیل و مدیریت
فاکتورها و جریان مالی مرتبط" — issuing, analyzing, and managing invoices
and related financial flow)

### Core deliverables
- New `invoice-employee` Employee definition, following the existing
  Employee/Tool/Run pattern used by Report Employee and Document
  Employee (see `11_Employee_Framework_v1.0.docx`,
  `58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md`,
  `63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md`).
- Invoice generation: structured invoice creation (line items, tax,
  currency, due dates) from tenant input or from a Document Employee
  output (e.g., an extracted contract/order).
- Invoice analysis: parsing/ingesting incoming invoices (reusing the
  Phase 5 OCR/document pipeline where applicable) and extracting
  structured fields.
- Financial-flow tracking tied to invoices: status (draft / sent / paid /
  overdue), and a per-tenant view of outstanding vs. collected amounts.
- PDF export of generated invoices (reusing the Phase 2 `reportlab`
  pipeline where practical, rather than introducing a second PDF
  toolchain).

### Explicitly out of scope for Phase 7
- Real accounting-system or ERP integrations (Roadmap §9 lists
  "همکاری با حسابداران و ERPها" as a parallel/marketing track, not a
  Phase 7 engineering deliverable).
- Any change to the Stripe billing/subscription path shipped in
  `v0.6.0` — invoices here are the Invoice Employee's own domain
  object, not `Subscription`/`Invoice` webhook objects from Stripe. If
  naming collision risk exists in code, this must be resolved before
  implementation (see Open questions).
- Multi-currency tax-rule correctness (VAT/سازمان مالیاتی-specific
  compliance rules) beyond storing a tax rate/amount as entered.

## Definition of Done (per Roadmap §11, applied to Phase 7)
A Phase 7 release is not considered closed until:
1. Invoice Employee is usable by a real tenant user end-to-end (create,
   analyze/ingest, export, status-track an invoice).
2. Backend unit tests for the new service/tools are added and passing in
   the build environment (mirroring the Phase 2/5/6 pattern of N new
   tests in a dedicated `test_invoice_service.py`).
3. A real-model E2E pass is obtained and user-reported, per the new
   convention established in `65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`.
4. An As-Built document (`67_PHASE_7_INVOICE_EMPLOYEE_AS_BUILT_v0.7.0.md`,
   next available number) and a `23_AS_BUILT_CURRENT_STATE_v0.7.0.md` are
   produced.
5. `CHANGELOG.md`, `backend/CHANGELOG.md`, `DEV_SETUP.md`, and
   `PROJECT_FILE_MANIFEST.json` are updated in the same release, per this
   project's established convention.

## Open questions to resolve before/at implementation start
- Naming collision: `backend/app/models/` likely needs an `Invoice`
  model distinct from any Stripe-facing invoice concept — confirm no
  symbol collision with `app/services/stripe_service.py` before coding.
- Whether invoice PDF export shares the Phase 2 `reportlab` template
  utilities directly or needs its own template module (recommendation:
  share, to avoid a second PDF toolchain — final call belongs to
  implementation, not this scope-lock document).

## Status of this document
This is a scope-lock only. No Phase 7 code has been written yet. It
exists so implementation starts from an agreed, written scope rather
than an ad hoc reading of the Roadmap — the same reason
`45_PHASE_1_SCOPE_LOCK_v0.2.34.md` was written for Phase 1.
