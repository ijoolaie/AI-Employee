# AI Employee Platform — Local Dev Setup (Step 1)

Goal: run **Backend v0.2.15** + **Frontend v0.1.2** and complete the flow:

**Register → Login → Create Employee → Start Run → See result**

---

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- (Optional) LM Studio with `google/gemma-4-e4b` for local AI calls; Anthropic is optional

---

## 1. Infrastructure

```bash
cd backend
docker compose up -d
# Wait until healthy: postgres :5432, redis :6379
```

## 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# includes psycopg2-binary for alembic

cp .env.example .env
# Edit .env:
#   SECRET_KEY=<long random string>
#   AI_DEFAULT_PROVIDER=lm_studio
#   AI_DEFAULT_MODEL=google/gemma-4-e4b
#   LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
# Do not put a real .env in the release ZIP.

alembic upgrade head

# Phase 2 — one-time seed for the Report Employee (creates the
# system Employee "report-employee"; safe to re-run, idempotent)
python scripts/seed_report_employee.py

# Terminal A — API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal B — Celery worker (required for Runs to leave "pending")
# Windows development uses Celery solo pool:
# celery -A app.workers.celery_app worker -l info --pool=solo
# Generic/Linux:
# celery -A app.workers.celery_app worker -l info
# Windows:
# python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok",...}`

API docs: http://localhost:8000/docs

## 3. Frontend

```bash
cd frontend
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
# → http://localhost:3000
```

## 4. Smoke test (UI)

1. Open http://localhost:3000 → redirected to **Register**
2. Create org:
   - Organization: `Demo Co`
   - Slug: `demo`
   - Email / password (min 8 chars)
3. Land on **Dashboard** (empty stats)
4. **Employees → New employee**
   - Name: `Hello Analyst`
   - Slug: `hello-analyst`
   - Prompt: `You are a helpful analyst. Reply briefly to the user message in the input.`
5. Open the employee → **Input (JSON)** e.g. `{"message": "Summarize Q1 sales in one sentence."}` → **Start run**
6. Run detail page polls while `pending` / `queued` / `running`
7. With LM Studio running and the model loaded: status should → `succeeded` + output JSON  
   With Anthropic selected but no API key: status → `failed` + error recorded (still correct behaviour)

Also verify: **Files** upload a small CSV, **Runs** list shows the run, **Settings** shows tenant slug `demo`.

## 5. Smoke test (API only, optional)

```bash
# Register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"tenant_name":"Demo","tenant_slug":"demo2","email":"a@b.com","password":"password12","full_name":"A"}' | jq

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@b.com","password":"password12","tenant_slug":"demo2"}' | jq -r '.data.access_token')

# Me
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN" | jq

# Create employee
EMP=$(curl -s -X POST http://localhost:8000/api/v1/employees \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"slug":"hello","name":"Hello","kind":"custom","prompt_template":"Say hi.","input_schema":{},"output_schema":{},"allowed_tools":[],"rules":{}}')
echo "$EMP" | jq
EMP_ID=$(echo "$EMP" | jq -r '.data.id')

# Create run
curl -s -X POST http://localhost:8000/api/v1/runs \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"employee_id\":\"$EMP_ID\",\"input_data\":{\"message\":\"hello\"}}" | jq
```

## Common issues

| Symptom | Fix |
|--------|-----|
| Run stuck on `pending` | Celery worker not running or Redis down |
| CORS errors in browser | Backend `CORS_ORIGINS` must include `http://localhost:3000` |
| 401 after refresh | Clear site data / localStorage key `aiep-auth` |
| Alembic fails | Postgres not up / wrong `DATABASE_URL` |
| Upload fails | Ensure `./var/storage` is writable (created on first upload) |

## Local AI

LM Studio is the default development provider. The server must expose the OpenAI-compatible API at `http://127.0.0.1:1234/v1` and the model `google/gemma-4-e4b` must be loaded.

## Version pins for this step

- Backend: **0.2.15-LMSTUDIO** (adds `employee_id` filter on `GET /runs`)
- Frontend: **0.1.0**
- Docs package: **v1.6**

---

When this flow works end-to-end, next step in order: **harden auth/error UX** (step 2).


---

## Step 3 notes (Run UX + Windows DX)

- Frontend shows a **pending** banner (start Celery) and a clearer **failed** banner (e.g. missing API key).
- Docs package **v1.4+**: bilingual fa/en locked for Phase 2 (`22_I18n_Localization`).
- Verified on Windows 10: Docker Postgres/Redis, Alembic after `down -v`, Celery `--pool=solo`, full Auth→Employee→Run→Files path.


## Windows Celery database lifecycle

The Run worker uses a worker-local SQLAlchemy `NullPool` session lifecycle to avoid asyncpg connections crossing the event loops created by `asyncio.run()`. Keep the Windows worker on `--pool=solo`.


## Current v0.2.13 validation note

Run input and output are now validated against the EmployeeVersion JSON Schemas using Draft 2020-12. Employee create/version-publish also validates the schema definitions. The real `.env` remains local-only and is not included in release ZIPs.


### v0.2.13 Prompt + Context Assembly
The current backend separates Employee prompt/context construction into `backend/app/ai/prompt_assembly.py`. RunService is orchestration-only at this boundary. The real `.env` remains local and is never included in release ZIPs.


## Latest cumulative verification — v0.2.15-LMSTUDIO

The latest verified Windows path is:

**POST /runs → pending → Celery `run.execute` → worker-local NullPool DB session → Prompt/Context Assembly → AI Gateway → LM Studio `/v1/chat/completions` → `ai_provider_calls` + `audit_logs` → Run `success` → COMMIT**

Verified with:

- LM Studio reachable at `http://127.0.0.1:1234/v1`
- model: `google/gemma-4-e4b`
- LM Studio smoke test: **PASS**
- authenticated `POST /api/v1/runs`: **201**
- Celery worker: **PASS**
- PostgreSQL access from worker: **PASS**
- LM Studio HTTP completion: **200**
- `ai_provider_calls` persisted: **PASS**
- `audit_logs` persisted: **PASS**
- Run output persisted with token usage and local cost `0.0 USD`: **PASS**
- Run transaction committed: **PASS**

The earlier Windows asyncpg/Proactor failure (`NoneType.send`) is addressed by `worker_db_session()` using a worker-local `NullPool`. Do not revert this isolation or replace it with the API pooled engine inside Celery tasks.

## v0.2.18 Usage reporting

The current baseline exposes a read-only tenant-scoped usage report at `GET /api/v1/usage/summary` and a Customer Panel page at `/usage`. It reads existing `ai_provider_calls` records and does not require a migration. The report is protected by the existing `audit.read` permission.

## v0.3.0 — Phase 2: Report Employee

New backend dependencies (already in `requirements.txt`): `pandas`,
`numpy`, `matplotlib`, `openpyxl`, `reportlab`. Re-run `pip install -r
requirements.txt` after pulling this version.

Quick manual check once the stack and `seed_report_employee.py` have run:

1. Log in to the customer UI, go to **Files**, upload a small CSV with at
   least one numeric column (and ideally a date column, to exercise the
   forecast).
2. Go to **Employees → Report Employee**, pick the uploaded file from the
   dropdown, click **Start run**.
3. Once the Run completes, its detail page shows a "Report Employee —
   downloads" card with PDF / Excel / chart buttons.

See `documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md` for the full
As-Built description and verification boundary.

## v0.4.0 — Phase 3: Validation tooling

After `alembic upgrade head` (picks up the new `feedback` table,
migration `b3c4d5e6f713`), the feedback loop is:

1. As a tenant user, complete a Report Employee Run, then rate it on the
   Run detail page ("Was this report useful?").
2. As a platform admin, open **Admin → Validation** to see, per tenant,
   Report Employee usage in the trailing 14 days and recorded feedback —
   this maps directly onto the Phase 3 exit criteria in
   `03_Roadmap_v1.1.docx` §6.

See `documents/59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md` for what
this dashboard does and — importantly — does not automatically decide.

## v0.5.0 — Phase 5: Document Employee

**New system packages required** (not installable via pip — install these
on the host/container before starting the backend):

```bash
# Debian/Ubuntu
sudo apt-get install -y tesseract-ocr tesseract-ocr-fas poppler-utils
```

`tesseract-ocr-fas` adds Persian OCR support; `poppler-utils` provides
`pdftoppm`, used by `pdf2image` to rasterize scanned PDF pages for OCR.
Without these, `document-employee` Runs on scanned PDFs/images will fail
at the `analyze_document` Tool step — native-text PDFs and DOCX/TXT files
do not require them.

After installing the system packages and `pip install -r requirements.txt`
(now including `pytesseract`, `pdf2image`, `pillow`), run the one-time
seed:

```bash
python scripts/seed_document_employee.py
```

Quick manual check:

1. Go to **Files**, upload a PDF, PNG/JPEG, or DOCX (a scanned/photographed
   document is a good test of the OCR fallback path).
2. Go to **Employees → Document Employee**, pick the file, **Start run**.
3. Once the Run completes, its detail page shows a "Document Employee —
   downloads" card with the extracted text.

See `documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md` for the
full As-Built description, the governance note about Phase 4/5 sequencing,
and the verification boundary.

## v0.6.0 — Phase 6: real Stripe payment provider

Set these environment variables (`.env`, never committed) to enable real
payments — the backend fails closed (clear errors, not silent no-ops)
until both `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are set:

```bash
STRIPE_SECRET_KEY=sk_test_...             # use a TEST key first
STRIPE_WEBHOOK_SECRET=whsec_...           # from the Stripe Dashboard webhook config
STRIPE_PRICE_MAP={"business":"price_...","professional":"price_..."}
STRIPE_CHECKOUT_SUCCESS_URL=http://localhost:3000/billing?checkout=success
STRIPE_CHECKOUT_CANCEL_URL=http://localhost:3000/billing?checkout=cancelled
STRIPE_PORTAL_RETURN_URL=http://localhost:3000/billing
```

In the Stripe Dashboard: create Products/Prices for the `business` and
`professional` plans (the free `starter` plan needs none), then register a
webhook endpoint at `https://<your-domain>/api/v1/webhooks/billing/stripe`
subscribed to at least `checkout.session.completed`,
`customer.subscription.updated`, `customer.subscription.deleted`, and
`invoice.payment_failed`.

**This step cannot be completed inside this delivery/build environment** —
it requires real network access to Stripe, which the sandbox that
produced this package does not have. Test it yourself, end-to-end, in an
environment that can reach `api.stripe.com`, before considering Phase 4's
commercial exit gate closed. See
`documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md` for the full
verification boundary and a step-by-step manual checklist.

## v0.6.1 — Real-model verification (documentation only, no setup change)

No new setup steps. This version records that `tests/test_ai_providers.py`
and the Document/Report Employee real-stack E2E flows were run against a
**real** LM Studio model (not the mocked provider used when tests run
inside the build sandbox) and reported as passing. The Anthropic provider
(`app/ai/providers/anthropic_provider.py`) was deliberately **not**
tested against the real Anthropic API in this round — treat it as
unverified until it's explicitly exercised. See
`documents/65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`.

Phase 7 (Invoice Employee) is scope-locked but not yet implemented — see
`documents/66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`. No new setup
steps exist for it yet; this section will be extended once that work
starts.


## Phase 7 — Invoice Employee seed

```bash
cd backend
python scripts/seed_invoice_employee.py
alembic upgrade head   # includes business_invoices
```

System employee slug: `invoice-employee`.


## Phase 8 — Order Employee seed

```bash
cd backend
python scripts/seed_order_employee.py
alembic upgrade head
```

Slug: `order-employee`.


## Phase 9 — Sales Employee seed

```bash
cd backend
python scripts/seed_sales_employee.py
alembic upgrade head
```

Slug: `sales-employee`.
API prefix: `/api/v1/sales`.
