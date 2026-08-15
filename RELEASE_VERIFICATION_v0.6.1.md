# AI Employee Platform — v0.6.1 Package Verification (real-model verification + Phase 7 scope lock)

This package makes no functional code changes beyond a version-string
consistency fix. It contains updated documentation, changelog, and the
regenerated file manifest on top of `v0.6.0`.

## What this release is
1. **Records a real-model (LM Studio) verification pass**, reported by
   the project owner, covering the AI Gateway provider tests
   (`test_ai_providers.py`) and the Document Employee / Report Employee
   real-stack E2E flows. The Anthropic provider was explicitly **not**
   tested, at the project owner's direction — it remains unverified.
   Full detail: `documents/65_REAL_MODEL_VERIFICATION_AS_BUILT_v0.6.1.md`.
2. **Scope-locks Phase 7 (Invoice Employee)** and resolves the Phase 6
   numbering collision flagged in `23_AS_BUILT_CURRENT_STATE_v0.6.0.md`.
   Full detail: `documents/66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md`.
   No Phase 7 code exists yet — that is the next work item.

## Important attribution note
The real-model test results in this release are **user-reported**, not
independently re-executed by the assistant. This delivery environment
has no network egress, so it cannot reach an LM Studio instance, a live
application stack, or any external API — the same constraint already
documented for the Stripe verification in `v0.6.0`. This package
documents what was reported, consistent with this project's existing
convention of marking such items `VERIFIED_USER_REPORTED_<date>` rather
than claiming direct verification.

## Source verification (this build environment)
- Python source compilation: PASS (including the `backend/app/main.py`
  version-string fix).
- Static Alembic head analysis: PASS — exactly one head (`0a1b2c3d4e5f`),
  unchanged. No new migration in this release.
- Backend unit test suite: **121 passed** in this build environment —
  unchanged from `v0.6.0` (this release adds no new automated tests; the
  real-model runs described above were executed outside this
  environment and are not part of the 121).

## Consistency fixes applied in this package
- `backend/app/main.py`: the FastAPI `version=` kwarg and both
  `/health`-style endpoints had been left at a stale `0.4.2` since before
  `v0.6.0` shipped as `0.6.0`. All three now read `0.6.1`, matching
  `backend/pyproject.toml` and `frontend/package.json`.
- `CHANGELOG.md` and `backend/CHANGELOG.md` both updated, prepended at
  the top per this project's newest-first convention.
- `PROJECT_FILE_MANIFEST.json` regenerated (paths, sizes, sha256 for
  every file in the package) and `verification_status` updated with the
  new real-model and Anthropic-deferral keys.

## What was NOT verified, and cannot be from this delivery environment
- The real-model claims in this release, beyond confirming the
  documents/manifest are internally consistent with what was reported.
- Anything already listed as unverified in `v0.6.0` (real Stripe API
  calls, MRR/paid-subscriber commercial gate, frontend build without
  `node_modules`, feedback/validation dashboard E2E).

## Release note
This release exists to keep documentation honest and current before
starting Phase 7: it records what the project owner actually verified
with a real model (and, just as importantly, what was deliberately left
untested — the Anthropic provider), and it locks the scope for Invoice
Employee before any of that code is written.
