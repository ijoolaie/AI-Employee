# Phase 13 — Agent Teams & Marketplace Design

**Status:** OPERATIONAL VALIDATION COMPLETE — LOCAL/RUNTIME EVIDENCE RECORDED  
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

Define a tenant-scoped reusable team containing:

- stable team identifier and version;
- member AgentDefinition references;
- role/skill metadata;
- execution policy and allowed tools;
- lifecycle status;
- immutable version identity.

### 13.2 Team Installation Boundary

Install a published team into a tenant through an explicit, authorized operation.

Installation must create tenant-local references without granting the installed team control-plane authority outside the tenant.

### 13.3 Team Execution Contract

Execute an installed team through the existing WorkItem/Agent execution substrate. Do not create a second task/lifecycle system.

Execution must retain:

- actor identity;
- tenant/workspace identity;
- correlation ID;
- approval state where required;
- audit events;
- cancellation and failure semantics.

### 13.4 Evaluation & Versioning

Support immutable team versions and evaluation records so published versions can be compared without mutating historical evidence.

Evaluation outputs are engineering/product evidence unless independently backed by external acceptance evidence.

### 13.5 Marketplace Boundary

Introduce a marketplace-facing publication/install contract with explicit ownership, visibility and tenant installation rules.

Marketplace publication must never imply customer acceptance, production deployment or trust beyond the recorded evidence.

## Recommended implementation order

1. TeamDefinition + immutable TeamVersion data model and migration.
2. Tenant-scoped authorization/service contract.
3. Team installation contract.
4. WorkItem-backed team execution orchestration.
5. Evaluation/version evidence.
6. Marketplace publication/discovery boundary.
7. Authorized UI surfaces.

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
