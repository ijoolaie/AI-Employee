# Change Log Package v1.5 — As-Built v0.2.14-LMSTUDIO

**Date:** 2026-08-07

This package records the v0.2.14 implementation delta while preserving the long-term architecture in the existing Product Vision, Master Plan and Roadmap documents.

## v0.2.14 — Hardened JSON Schema Validation

- Draft 2020-12 runtime validation is now the stable Employee input/output contract boundary.
- `FormatChecker` enables declared JSON Schema format assertions.
- Local JSON Pointer references are supported.
- External `$ref` and `$dynamicRef` resources are rejected to prevent unintended network/filesystem resolution from tenant-controlled schemas.
- Validation details include field, instance path, schema path, validator, message and validation version.
- Secondary validation errors are bounded to five entries.
- Added focused tests for nested constraints, enums, local references, external-reference rejection and format validation.
- Backend version is `0.2.14`.

## Verification

- `tests/test_schema_validation.py`: **10 passed**.
- Full pytest collection in the packaging environment: **blocked** by missing `python-jose` dependency; source/dependency requirements remain declared in `backend/requirements.txt`.
- Windows LM Studio/PostgreSQL/Redis/Celery E2E remains the authoritative runtime verification path.

## Secrets policy

The real `.env` is intentionally excluded from all release ZIPs. Only `.env.example` is shipped.
