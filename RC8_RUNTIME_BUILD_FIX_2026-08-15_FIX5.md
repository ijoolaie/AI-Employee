# RC8 Runtime Build Fix 5 — 2026-08-15

Fixed the next frontend contract/build blockers found by the real Docker production build.

## Fixes
- Admin Operations: removed invalid `DeadLetter.status` access and display `kind` + `attempts`, matching `frontend/types/index.ts`.
- Customer Channels: memoized the `employees` fallback to satisfy `react-hooks/exhaustive-deps`.
- Public Chat: derived `conversationId` and used it as the polling effect dependency, eliminating the stale `conversation` dependency warning without recreating the interval on unrelated conversation object changes.

The previous i18n and invoice fixes are retained.
