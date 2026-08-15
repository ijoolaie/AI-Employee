# RELEASE v0.4.1 — OUTBOX HARDENING — AS-BUILT

## Status
As-Built release synchronization for the Phase 3 validation-tooling baseline. This document records the v0.4.1 hardening changes actually present in the package. It does **not** claim that Roadmap Phase 4 (Monetization) is complete.

## What v0.4.1 changes

- Clarifies the durable Outbox lifecycle: workflow messages are terminally marked `dispatched` when Celery accepts the task; `email.send` remains `processing` until the email worker completes the SMTP side effect.
- Adds the OpenTelemetry `outbox.status=queued` attribute to the email handoff path.
- Preserves the existing transactional claim/retry/dead-letter flow.
- Adds regression coverage in `backend/tests/test_v041_outbox_hardening.py`.
- Aligns application/package version reporting to `0.4.1`, including FastAPI metadata, `/health`, `/health/dependencies`, backend package metadata, and frontend package metadata.

## Runtime verification evidence

On 2026-08-09, the real Docker stack was observed with PostgreSQL 16, Redis 7, Celery Worker and Celery Beat running. Three `workflow.execute` Outbox messages were persisted as `dispatched`; the Celery worker received all three tasks; all three corresponding Workflow Runs completed with `success`; and each `hello` WorkflowStepRun completed with `success`.

This runtime evidence is user-reported evidence from the development environment, not an independently reproduced execution by this packaging environment.

## Verification boundary

- `python -m compileall app scripts`: PASS in the packaging environment.
- The local packaging environment cannot run the complete pytest suite because required runtime packages such as `asyncpg` and `python-jose` are unavailable there.
- The user's live Docker environment has already verified the workflow Outbox → Celery → Workflow execution path.
- Frontend production build remains environment-dependent and was not run in the packaging environment.

## Roadmap gate

The Roadmap defines **Phase 4 — Monetization** as: Starter/Business/Professional plans, complete Billing + Usage Tracking, a clear upgrade path, and positive/growing MRR with a defined paid-subscriber minimum. v0.4.1 does not implement those business outcomes. Existing Usage is reporting-only; quotas, invoicing, subscriptions and payment enforcement remain future work.

Therefore: **the release hardening work is complete, but Roadmap Phase 4 is not complete and Phase 5 (Document Employee) should not be started as a formal roadmap phase yet.**
