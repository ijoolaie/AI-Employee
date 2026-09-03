# Phase 13 — Agent Teams & Marketplace Design

**Status:** IMPLEMENTED — AUTHORIZED UI + E2E ACCEPTANCE MERGED  
**Date:** 2026-09-03

## Scope

Phase 13 productizes reusable Agent Teams and Marketplace capabilities on top of the existing Human + Agent execution model.

The implementation remains contract-first and preserves the platform's existing execution, authorization, tenancy, audit and evidence boundaries rather than introducing a parallel execution path.

## Non-negotiable boundaries

Every Phase 13 capability preserves:

- tenant isolation at backend/service boundaries;
- RBAC and scoped API-key authorization;
- policy and approval controls for risky actions;
- scoped tools and credentials;
- audit/history and correlation identifiers;
- lifecycle, cancellation and concurrency safety;
- explicit evidence boundaries;
- compatibility with existing Employee-backed capabilities;
- one authoritative Alembic migration graph.

## Implemented product slices

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

Implemented and merged to `main`. The Marketplace surface provides authenticated discovery of public publications, workspace-scoped installation review, tenant-local installation result/provenance and explicit install/acceptance/deployment boundary messaging. Backend authorization remains authoritative.

### 13.7 End-to-End Product Acceptance

Implemented and merged to `main` in PR #257. Playwright browser acceptance covers authenticated Marketplace discovery, workspace-scoped review, tenant-local installation success UX, explicit installation/acceptance/deployment boundaries, and authorization failure handling.

The browser test uses deterministic Playwright network interception. Backend authorization and tenant isolation remain authoritative in the Marketplace service/API tests; this E2E slice does not claim a live cross-tenant production integration environment.

## Definition of Done

Phase 13 engineering completion is evidenced by:

- backend-enforced tenant/RBAC boundaries;
- unit and integration coverage;
- concurrency/lifecycle coverage where applicable;
- audit coverage;
- migration graph validation;
- CI and CodeQL coverage, with Architecture Guard/operational workflows applied where their path triggers require them;
- authorized customer UI;
- deterministic browser acceptance;
- explicit local/CI/production evidence classification.

## Operational gate

The Phase 13 operational gate was previously validated in the local Docker runtime for Test Center worker execution, stale-run expiration and audit emission. That record remains local/runtime evidence and does not constitute production acceptance.

## Phase 13 CI/E2E evidence — 2026-09-03

- Marketplace import backend PR #255 merged successfully after CI, CodeQL, Architecture Guard, Production Observability and Production Rollback & Alerting gates passed.
- Authorized Marketplace UI PR #256 merged successfully; CI and CodeQL were observed for its head, while workflow applicability varies by path trigger.
- Marketplace E2E acceptance PR #257 merged successfully at merge commit `065a92a948734a28baf9ccaaa66dbb6905e0401e`.
- PR #257 head `5119756cdde64bee3e60baef91eb2ca7f62bcac8` had successful CI and CodeQL runs before merge.

## Evidence boundary

These repository and local-runtime records are engineering evidence. They do not establish external production deployment, live third-party provider validation, customer acceptance, commercial go-live or production certification. Those remain **EXTERNAL-PENDING** until independently evidenced.
