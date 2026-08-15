# AI Employee Platform — v0.7.0 Package Verification

## What this release is
Phase 7 Invoice Employee (`BusinessInvoice` domain), tools, REST API, seed, unit tests, As-Built docs.

## Automated verification (this build environment)
- Python compile of `backend/app`: PASS
- Backend unit suite: **77 passed** (includes `test_invoice_service.py` and updated tool-registry contract)
- Frontend contract suite: **28 passed** (`scripts/test-frontend-contract.mjs`)

## Not executed here (requires local stack)
- `alembic upgrade head` against a live Postgres
- Celery worker + real LM Studio E2E Run of `invoice-employee`
- Stripe live network calls

User should run on their machine:
```bash
cd backend && alembic upgrade head && python scripts/seed_invoice_employee.py
pytest tests/ -q
# then API + worker + one real Run against invoice-employee
```

## Phase 7 DoD
1. Code usable end-to-end on local stack — code ready; user E2E recommended
2. Unit tests — PASS
3. Real-model E2E — still **user-reported** when run locally
4. As-Built docs — present
5. CHANGELOG / DEV_SETUP — updated
