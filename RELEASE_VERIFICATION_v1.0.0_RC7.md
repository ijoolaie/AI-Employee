# Release Verification — v1.0.0 RC7

## Scope

Production certification and launch-readiness hardening over RC6.

## Implemented

- Security response headers.
- Production configuration safety validation.
- CI certification workflow.
- Docker stack smoke verification.
- k6 smoke workload.
- Environment certification gate.
- Launch/security/GDPR/performance checklist.
- Frontend RC7 contract coverage.
- Version bumped to `1.0.0-rc.7`.

## Local verification performed in handoff environment

- Python source compilation: PASS.
- Frontend static contract script: available; full execution requires npm dependencies.
- Production certification environment gate: available; external credentials are intentionally not embedded.
- Full backend test suite: BLOCKED in this handoff environment because `asyncpg` and `python-jose` are not installed in the runtime image.
- Full Next.js build: BLOCKED in this handoff environment because `node_modules` is not present and dependency installation timed out.

## Certification rule

A PASS for Shopify, Stripe, WhatsApp, PostgreSQL/Redis, or a production build must come from the target staging/CI environment. No simulated PASS is accepted.
