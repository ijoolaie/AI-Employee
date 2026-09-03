# Phase 13 — Authorized UI Slice

Date: 2026-09-03

## Scope

The first authorized UI surface connects the existing customer Test Center page to the Phase 13 Test Center worker execution boundary.

## Behavior

- The existing tenant-scoped Test Center page remains the entry point.
- Selecting **Run** creates a queued Test Run through the existing API contract.
- The UI immediately dispatches that queued run through `POST /test-center/runs/{run_id}/execute`.
- The page polls queued/running history every three seconds and exposes the existing evidence and verification-record actions.
- No client-side execution or arbitrary test-code execution is introduced.

## Evidence boundary

The UI only initiates and observes the backend execution contract. Execution remains server-side in the Celery Worker. Runtime validation remains classified as local/runtime evidence unless independently backed by production or customer acceptance evidence.

## Definition of Done

- Existing tenant-scoped API boundary is reused.
- UI dispatch uses the backend authorization boundary rather than a direct broker call.
- Worker execution and lifecycle remain authoritative.
- Existing audit/correlation/evidence behavior is preserved.
- Frontend lint/build/contract checks are required before merge.
