# RC8 Runtime E2E Fix8 — 2026-08-15

## Scope
- Corrected stale Playwright critical-flow routes (`/auth`, `/customer/*`) to match the actual Next.js route groups (`/login`, `/dashboard`, `/admin`).
- Added smoke coverage for `/login`, `/forgot-password`, and `/reset-password`.
- Added frontend contract coverage ensuring password recovery UI and API wiring remain aligned.

## Important
This change improves the test/contract layer. It does not claim that SMTP delivery is configured; real password-reset email delivery still depends on the staging SMTP environment variables.
