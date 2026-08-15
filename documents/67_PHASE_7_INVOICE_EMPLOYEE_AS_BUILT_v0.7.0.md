# Phase 7 As-Built — Invoice Employee (v0.7.0)

## Status
Implemented against `66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.

## Open questions resolved
1. **Naming:** domain model is `BusinessInvoice` / table `business_invoices` — no collision with Stripe subscription billing.
2. **PDF toolchain:** reuses `reportlab` (same stack as Report Employee).

## Delivered
- Model + Alembic migration `a0b1c2d3e4f7`
- `app/services/invoice_service.py` — create, status, list, summary, analyze file, export PDF
- Tools: `create_invoice`, `update_invoice_status`, `analyze_invoice_file`, `export_invoice_pdf`, `invoice_financial_summary`
- REST API `/api/v1/invoices` (list/get/create/status/export-pdf/summary)
- Seed script `scripts/seed_invoice_employee.py` (slug `invoice-employee`)
- Unit tests `tests/test_invoice_service.py`

## Explicitly still out of scope
- ERP/accounting integrations
- Stripe path changes
- Jurisdiction-specific tax engine beyond stored tax_rate

## DoD checklist
1. E2E usable by tenant — requires local seed + Run against invoice-employee (user-reported real-model pass still required)
2. Unit tests added
3. Real-model E2E — user-reported (pending)
4. This As-Built + current-state note
5. CHANGELOG / DEV_SETUP updates in same package


## Amendment v0.7.1 — tax_rate normalization

After real LM Studio E2E, the model passed `tax_rate: 0.09` meaning 9%, while the service treated values as percent points (0–100). That produced tax 0.27 instead of 27.

**Fix:** `normalize_tax_rate()` in `invoice_service`:
- values in `(0, 1]` → interpreted as fraction → stored as percent (`0.09` → `9.00`)
- other values in `[0, 100]` → percent points as-is (`9` → `9`)

Tool schema description and API schema description updated. Unit tests cover both forms.

Verified on local stack (user-reported): create_invoice + export-pdf + summary against LM Studio `google/gemma-4-e4b`.
