# Phase 13 — Agent Teams & Marketplace Design

**Status:** DESIGN STARTED / IMPLEMENTATION GATED BY OPERATIONAL VALIDATION  
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
