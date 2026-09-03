# Phase 13 — Agent Teams & Marketplace Design

**Status:** BACKEND FOUNDATION IMPLEMENTED — MARKETPLACE IMPORT BOUNDARY ADDED  
**Date:** 2026-09-03

## Scope

Phase 13 productizes reusable Agent Teams and Marketplace capabilities on top of the existing Human + Agent execution model.

The first implementation slice is intentionally contract-first. It must preserve the platform's existing boundaries rather than introduce a parallel execution path.

## Non-negotiable boundaries

Every Phase 13 capability must preserve:

- tenant isolation at backend/service boundaries;
- RBAC and scoped API-key authorization;
- policy and approval controls for risky actions;
- scoped tools and credentials;
- audit/history and correlation identifiers;
- lifecycle, cancellation and concurrency safety;
- explicit evidence boundaries;
- compatibility with existing Employee-backed capabilities;
- one authoritative Alembic migration graph.

## Initial product slices

### 13.1 Team Definition Contract

Implemented with tenant-scoped `TeamDefinition` and immutable `TeamVersion` contracts and migrations.

### 13.2 Team Installation Boundary

Implemented through `TeamInstallation` and an authorized tenant-local installation service/API. Same-tenant installation remains available for existing team definitions.

### 13.3 Team Execution Contract

Implemented through the existing WorkItem/Agent execution substrate. Installed teams dispatch member work through canonical Agent execution rather than a parallel task lifecycle.

### 13.4 Evaluation & Versioning

Implemented with immutable `TeamEvaluation` records tied to immutable `TeamVersion` identities.

### 13.5 Marketplace Boundary

Implemented with publication/discovery metadata and an explicit authorized import operation.

A public publication can be imported into another tenant only through `marketplace.install`. Import creates tenant-local copies of the TeamDefinition, TeamVersion and referenced AgentDefinitions, records the source publication on `TeamInstallation`, and emits an audit event. No AgentInstance is created automatically; target-tenant provisioning remains an operational responsibility.

Marketplace publication/import does not imply customer acceptance, production deployment or trust beyond recorded evidence.

### 13.6 Authorized UI

**NOT YET IMPLEMENTED for Teams/Marketplace.** The next product-facing slice is an authorized UI consuming the backend contracts without reimplementing authorization in the browser.

## Recommended implementation order

1. TeamDefinition + immutable TeamVersion data model and migration. **DONE**
2. Tenant-scoped authorization/service contract. **DONE**
3. Team installation contract. **DONE**
4. WorkItem-backed team execution orchestration. **DONE**
5. Evaluation/version evidence. **DONE**
6. Marketplace publication/discovery/import boundary. **DONE — backend**
7. Authorized UI surfaces. **NEXT**

## Definition of Done

A Phase 13 slice is not complete until it has:

- backend-enforced tenant/RBAC boundaries;
- unit and integration coverage;
- concurrency/lifecycle coverage where applicable;
- audit coverage;
- migration graph validation;
- CodeQL/CI/Architecture Guard coverage;
- explicit local/CI/production evidence classification.

## Operational gate

This design may proceed while Phase 12 operational validation is pending, but Phase 13 production-facing implementation must not be declared complete until Test Center worker execution, stale-run expiration, audit emission and observability have been validated in an actual runtime environment.

## Operational Validation Record — 2026-09-03

The Phase 13 operational gate was validated in the local Docker runtime after the Test Center execution worker was merged.

### Runtime environment

- Docker Compose services: PostgreSQL, Redis, API, Celery Worker and Celery Beat.
- Database rebuilt from the authoritative Alembic graph and migrated to head `p13_05_marketplace_boundary`.
- Worker and Beat images were rebuilt from the merged `main` revision.
- Registered Celery tasks were verified in the live Worker image:
  - `test_center.execute_run`
  - `test_center.expiration_sweep`

### Execution lifecycle evidence

A tenant-scoped Test Center run was created through the API and dispatched through the execution endpoint. The actual local runtime path was:

`API create → API dispatch → Celery → Worker → started → passed → audit`

The Worker executed the safe backend contract executor and recorded a passed result with the expected definition code, worker executor identity, fixture validation and correlation identifier.

Audit events recorded for the execution lifecycle included:

- `test_run.queued` — user actor;
- `test_run.dispatched` — user actor, with Celery task ID and correlation ID;
- `test_run.started` — system actor, source `celery_worker`;
- `test_run.passed` — system actor, source `celery_worker`, with evidence boundary `engineering_product_evidence`.

### Stale-run expiration evidence

A queued Test Center run was made stale beyond the configured `test_center_run_timeout_seconds` value and was subsequently expired by the scheduled Beat/Worker sweep.

The observed runtime path was:

`Celery Beat → test_center.expiration_sweep → Worker → queued run expired`

The run transitioned to `expired`, received `finished_at`, and recorded the expected `test run expired` error. The corresponding `test_run.expired` audit event identified `source=celery_beat`, the correlation ID and the configured timeout.

### Observability and evidence boundary

The runtime logs provide direct evidence that Celery Beat dispatched the expiration sweep and that the Worker received and successfully completed both the expiration and execution tasks.

The repository's Prometheus metrics are process-local. The API `/metrics` endpoint does not expose the live prefork Worker's in-memory counter, and a newly spawned inspection process cannot be used as evidence of the already-running Worker's counter value. No direct Worker metric sample is therefore claimed here.

This is intentional evidence classification:

- **Local/runtime evidence:** Docker service health, Celery task registration, Beat dispatch logs, Worker receipt/completion logs, database lifecycle state and audit records.
- **CI evidence:** repository workflow checks such as CI, CodeQL and Architecture Guard where applicable.
- **Production evidence:** **not established by this validation record**.

### Executor boundary

The Test Center execution Worker currently uses a safe backend contract/probe executor. It does **not** execute arbitrary test code supplied by a Test Definition. This runtime validation proves the Worker execution/lifecycle boundary, not a general-purpose arbitrary-code test execution platform.

### Gate conclusion

The required Test Center runtime execution, stale-run expiration and audit emission paths have been validated in an actual local runtime environment. Observability is evidenced through runtime logs and persisted audit/lifecycle state, with the Worker Prometheus metric exposure limitation explicitly recorded above.

Accordingly, the operational gate is **validated for local/runtime evidence**. This record does not constitute production acceptance, production deployment evidence or customer acceptance evidence.
