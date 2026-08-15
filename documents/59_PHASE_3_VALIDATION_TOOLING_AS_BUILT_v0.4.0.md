# PHASE 3 — VALIDATION — AS-BUILT — v0.4.0

## Status of this document
As-Built (describes what was actually implemented), not a plan. Follows
the verification rule from `documents/45_PHASE_1_SCOPE_LOCK_v0.2.34.md`.

## A necessary scoping note
Per `03_Roadmap_v1.1.docx` §6, Phase 3 ("Validation") is **not an
engineering phase**:

> هدف: ۳ تا ۵ مشتری واقعی (نه بیشتر). این مشتری‌ها: باگ‌ها و نقاط ضعف را
> پیدا می‌کنند؛ پیشنهاد بهبود می‌دهند؛ مسیر اولویت‌بندی توسعه را مشخص
> می‌کنند؛ اولین Case Studyها را می‌سازند.
> معیار اتمام فاز: حداقل ۳ مشتری فعال که به‌طور منظم از Report Employee
> استفاده می‌کنند و بازخورد کیفی ثبت شده است.

Its Definition of Done is a **business/customer-development outcome**
(real people, using the real product, regularly, with feedback recorded) —
not a code artifact. This package cannot manufacture real customers or
real usage, and does not claim to. What this release does is build the
**product tooling Phase 3 needs to actually be executed and tracked**,
so the team is not doing customer validation by spreadsheet.

## What was implemented

### 1. Feedback capture (`app/models/feedback.py`, `app/api/v1/feedback.py`)
A `feedback` table (tenant-scoped, optional link to a `Run`/`Employee`,
1–5 `rating` + free-text `comment`, `category` of `run` or `general`) with
`POST /api/v1/feedback` (any tenant user with the new `feedback.create`
permission — seeded onto the tenant Admin role like every other Phase 1/2
permission) and `GET /api/v1/feedback` (`feedback.read`, tenant-scoped
list). This is the "بازخورد کیفی ثبت شده" (recorded qualitative feedback)
half of the Phase 3 exit criterion, made structurally real instead of
living in email or a spreadsheet.

### 2. Validation dashboard (`app/services/feedback_service.py`, `GET /api/v1/admin/validation`)
A platform-admin-only aggregate view (`admin.py`, reusing the existing
`PlatformAdminContext` — `is_platform_admin` gate, unchanged from Phase 1)
that computes, per tenant:
- `report_employee_runs_last_14d` — the "مشتری فعال ... به‌طور منظم"
  (regularly active customer) proxy: at least one Run of the
  `report-employee` System Employee in a trailing 14-day window
  (`ACTIVE_WINDOW_DAYS`, a named constant, not a buried magic number).
- `report_employee_runs_total`, `last_run_at`, `feedback_count`,
  `avg_rating`.

And platform-wide: `active_tenant_count`, and
`meets_phase3_customer_criteria` — a direct boolean check against the
Roadmap's own "≥3" target (`PHASE3_CUSTOMER_TARGET = 3`), plus the 20 most
recent feedback entries across all tenants.

**This is explicitly a proxy metric, not a completion switch.** A tenant
with 14 automated Runs and zero human engagement would count as "active"
by this query; the dashboard's own footer text says so. Judging Phase 3
complete is a product decision informed by this data plus actually reading
the feedback comments — not something this endpoint decides for the team.

### 3. Frontend
- `app/(customer)/runs/[id]/page.tsx`: a star-rating + comment widget
  appears on successful Runs ("Was this report useful?"), posting to
  `POST /api/v1/feedback` with `category: "run"`.
- `app/(admin)/admin/validation/page.tsx`: new admin page — KPI cards
  (active tenants / target, criteria met Y/N, feedback count, average
  rating), a per-tenant activity table, and a recent-feedback feed.
  Linked from `AdminSidebar` ("Validation").
- `lib/api.ts`: `submitFeedback()`, `getValidationSummary()`, and the
  associated TypeScript interfaces.

## Explicitly NOT implemented / NOT claimed
- **Phase 3 is not marked complete by this release.** No real customer
  data exists in a delivery-environment build; `active_tenant_count` will
  read `0` until real tenants actually run the Report Employee repeatedly.
- **No outreach/CRM tooling** (contacting the 3–5 target customers,
  scheduling calls, tracking case-study production) — out of scope for a
  code repository; that is direct founder/sales work per the Roadmap's own
  framing ("۳ تا ۵ مشتری دستی" — handpicked, not self-serve funnel).
- **No automated NPS/CSAT survey cadence** — feedback capture is
  opportunistic (post-Run prompt) only; a scheduled re-engagement survey
  is DEFERRED.
- **No case-study export/template** — the Roadmap lists "اولین Case
  Studyها" as a Phase 3 output; producing one is a writing/marketing task,
  not something this dashboard automates. DEFERRED.

## Verification boundary
- Python source compilation: PASS (`python3 -m compileall app scripts`).
- Backend unit test suite: **97 passed** in this build environment (91
  carried over from v0.3.0 + 6 new in `tests/test_feedback_schema.py`).
  The new tests are DB-independent (Pydantic contract only, same rationale
  as `test_rbac.py`) — `feedback_service.create_feedback()` and
  `validation_summary()`'s DB-backed logic are **NOT** exercised by unit
  tests in this build; they require PostgreSQL.
- `tests/test_v036_e2e_contract.py::test_migration_merge_has_single_revision`
  was updated to assert the new head `b3c4d5e6f713` (was `7a2b3c4d5e6f`) —
  flagged explicitly, same convention as the Phase 2 tool-registry test
  update.
- Static Alembic head analysis: exactly one head, **`b3c4d5e6f713`**
  (`7a2b3c4d5e6f` → `b3c4d5e6f713`, adds the `feedback` table only — no
  other schema changes).
- Real PostgreSQL E2E for `POST /api/v1/feedback` and
  `GET /api/v1/admin/validation`: **NOT VERIFIED** in this delivery
  environment (no live services here). Run `alembic upgrade head` and
  exercise both endpoints against a real database before relying on the
  Validation dashboard.
- Frontend: TypeScript source follows existing shipped patterns; `next
  build` NOT run in this environment (no `node_modules`).

## Package/version bump
- `backend/pyproject.toml`: `0.3.0` → `0.4.0`.
- `frontend/package.json`: `0.3.0` → `0.4.0`.
- `app/main.py` FastAPI `version=` bumped to `0.4.0`.

## Recommended next step (not part of this delivery)
Run `alembic upgrade head` against a real database, then actually use the
in-product feedback widget with the 3–5 real customers the Roadmap calls
for, and check `/admin/validation` periodically rather than assuming Phase
3 completion from this document alone.
