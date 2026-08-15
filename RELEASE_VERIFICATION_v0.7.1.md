# v0.7.1 Verification

## Fix
tax_rate normalization after LM Studio E2E where model passed 0.09 for 9%.

## Tests (build environment)
- `pytest tests/test_invoice_service.py` and full suite expected green
- Frontend contract unchanged

## User-reported E2E (v0.7.0 base, before patch)
- verify_lm_studio PASS
- Run invoice-employee → success, invoice persisted, PDF export, summary
