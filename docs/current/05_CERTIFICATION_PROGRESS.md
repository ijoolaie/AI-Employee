# Certification Roadmap Progress

## Status as of 2026-08-19

**Current state: GREEN — full certification stack-smoke and product acceptance gates passed. Production deployment hardening remains.**

Latest verified runtime checkpoint:
- GitHub Actions Production Certification run: `32276463633` (run #100)
- Architecture Guard: `32276462650` — SUCCESS
- Production Compose Validation: `32276462622` — SUCCESS
- Production Certification: `32276463633` — SUCCESS

## Current certification path — COMPLETE

The current workflow passed, in one run:

1. Python/npm dependency setup with CI caches
2. Playwright Chromium installation without host `apt` dependency installation
3. Python compilation and Ruff
4. Compose-managed PostgreSQL and Redis readiness
5. Alembic migration
6. Backend tests excluding the container-only OCR marker
7. Frontend contract tests, unit tests and production build
8. Production-like Docker stack startup/readiness
9. OCR runtime and Farsi language verification inside the API container
10. OCR extraction test inside the API container
11. Backend dependency E2E
12. Auth P0
13. Tenant isolation + RBAC P0
14. Employee -> Run -> AI -> Result
15. Files -> Knowledge -> Memory
16. Admin / Developer API Keys
17. Workflow -> Approval -> Schedule
18. Orders -> Sales -> Invoice -> Billing
19. Frontend Playwright E2E
20. Stack cleanup

**All of the above passed in Run `32276463633`.**

## Certification debugging lessons captured

The certification cycle found and fixed infrastructure/application issues rather than weakening assertions:

- Playwright system-dependency installation was removed from CI; Chromium is installed without `--with-deps`.
- PostgreSQL/Redis GitHub service containers were removed so Docker Compose is the single certification stack and cannot conflict on ports.
- OCR is verified in the production-like API container instead of requiring Tesseract on the host runner.
- OCR-dependent pytest coverage is marked `requires_ocr` and executed inside the API container.
- Memory creation now supplies an explicit `effective_at` timestamp.
- Sales deal creation/transaction behavior was corrected so the subsequent stage operation sees committed state.
- `requires_ocr` is registered in pytest configuration.

## Important current evidence

The latest green run demonstrates fresh real-stack evidence for Files / Knowledge / Memory and Admin / Developer API Keys. These areas must no longer be described as merely historical or unverified for this certification branch.

## Production hardening checkpoint

The repository-level certification is **not the same as production deployment certification**. The following still require deployment-specific evidence:

1. HTTPS/reverse proxy and trusted-origin configuration.
2. Production secrets supplied through the deployment secret manager.
3. Production PostgreSQL/Redis/Celery endpoints and network exposure.
4. Worker and beat operation, restart policy and queue health.
5. Monitoring, centralized logging, OTel exporter configuration and alerting.
6. Persistent storage, backup/restore and recovery verification.
7. Production payment/webhook secrets and signature verification where enabled.
8. Deployment-specific security review and least-privilege infrastructure configuration.
9. Clean production migration/rollback rehearsal.
10. External integrations such as SMTP/object storage/live provider credentials where enabled.

## Next roadmap phase

Do not reopen already-passed certification gates unless a later code/configuration change affects them. Continue with production hardening and deployment evidence.

1. Verify the production configuration guard with safe and unsafe representative settings.
2. Audit deployment manifests/reverse proxy and secret injection.
3. Verify worker/beat, observability, storage and backup/restore controls.
4. Verify external integration configuration where enabled.
5. Perform deployment/rollback rehearsal.
6. Run the final certification after relevant production-hardening changes.
7. Keep this document updated with the new run ID and evidence.

## Operating rule

**A green certification gate is the checkpoint; a failed later gate is the next task. Do not modify already-passing behavior merely to make a later gate pass.**
