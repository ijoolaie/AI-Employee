# Phase 1 Scope Lock — v0.2.34

## Purpose
This document resolves scope ambiguity between historical roadmap/frontend documents and the current implementation plan. Phase 1 is considered complete only when the Core, operational hardening, observability, and required management surfaces listed below are implemented and verified.

## Phase 1 mandatory scope

### Core/runtime
- Auth/JWT, tenant isolation, RBAC
- Employees and versioning
- AI Gateway and provider abstraction
- LM Studio E2E
- Prompt/context assembly, validation, RAG and memory foundations
- Tool registry, authorization and human approval
- Workflow engine, conditions, schedules, events/webhooks
- Workflow versioning
- Parallel execution
- Retry/recovery
- Timeout/cancellation
- Global idempotency
- Transactional outbox
- Dead-letter queue
- Replay/compensation

### Observability/operations
- Audit log
- Trace
- Cost tracking
- Metrics
- Queue/outbox metrics
- Correlation IDs
- OpenTelemetry export
- PostgreSQL migration verification
- Redis/Celery failure/recovery verification
- LM Studio end-to-end verification

### Security
- Webhook secret rotation
- Secret encryption at rest
- Rate limiting
- Payload-size limits
- Replay protection
- Endpoint permission audit
- Tenant-isolation verification

### Management surfaces
- Customer dashboard
- Workflow management UI
- Approval UI
- Schedule UI
- Webhook UI
- Admin dashboard / Admin panel
- Visual Workflow Builder
- Developer/observability console surfaces required by the approved UX scope

## Verification rule
A feature is not considered complete merely because documentation or a placeholder exists. It must be marked one of:

- IMPLEMENTED — code exists
- VERIFIED — automated or E2E verification passed
- PARTIAL — some implementation exists but acceptance criteria are incomplete
- DEFERRED — explicitly moved out of Phase 1 by a later approved decision

## Historical document reconciliation
Historical roadmap/frontend documents remain immutable references. This scope-lock document is the current execution contract for Phase 1. Where historical text says a surface was deferred but the approved current Phase 1 scope includes it, the current scope wins and the historical document is not rewritten.

## v0.2.34 implementation note
v0.2.34 begins the management-surface completion track by adding a Workflow catalog/detail UI backed by the existing workflow execution and observability APIs, and exposes Workflow navigation in the Customer panel. Backend workflow listing is now available through `GET /api/v1/workflows`.


## v0.2.35 execution update
Security hardening track implemented at code level: Redis-backed rate limiting, webhook payload limits, timestamp-based replay protection, and webhook secret rotation. Remaining status is subject to live PostgreSQL/Redis and full E2E verification.


## Current implementation status — v0.2.38
Workflow Versioning is now implemented as an immutable execution contract. Runs pin WorkflowVersion and snapshot resolved EmployeeVersion dependencies; Replay uses the exact source version/contract. Live PostgreSQL trigger verification remains pending until the real database stack is available.
