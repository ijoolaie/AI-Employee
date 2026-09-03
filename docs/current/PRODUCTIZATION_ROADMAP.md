# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-03

V1.4 remains the frozen architecture foundation. V1.5 is the active Human + Agent operating-model extension.

Phase 11 Unified Execution acceptance is complete. Phase 12 Test Center & Evidence Platform is implemented through P12.6, including the authorized customer UI and automatic stale-run expiration sweep. The Phase 13 Agent Teams & Marketplace backend foundation is now implemented through the marketplace publication/import boundary; authorized UI and end-to-end product acceptance remain next.

## Product direction

The platform is evolving toward shared business execution contracts in which Humans and specialized Agents operate under the same core boundaries:

- tenant isolation;
- authorization/RBAC;
- policy and approval;
- scoped tools;
- audit/history;
- lifecycle and concurrency controls.

Existing Employee-backed functionality remains compatible while changed capabilities migrate incrementally.

## Phase status

### Phase 8 — Unified Execution Foundation
**COMPLETE / VERIFIED FOUNDATION.** Human and Agent execution, lifecycle and concurrency hardening form the shared execution substrate.

### Phase 9 — Platform Command Center
**IMPLEMENTED / HARDENING CONTINUES.** Role-specific Platform operations are implemented; ongoing work validates runtime behavior.

### Phase 10 — Reseller Operations Workspace
**IMPLEMENTED / HARDENING CONTINUES.** Role-aware reseller operations are implemented; runtime validation continues.

### Phase 11 — Client Business Workspace / Unified Execution Acceptance
**COMPLETE.** Real-stack Human and Agent WorkItem acceptance passed with zero failed product gates.

### Phase 12 — Test Center & Evidence Platform
**IMPLEMENTED / OPERATIONAL HARDENING.**

#### P12.1 — Test Definition Contract
**IMPLEMENTED / VERIFIED.** Tenant-scoped definitions with typed prerequisites, expected results and evidence requirements.

#### P12.2 — Safe Test Execution
**IMPLEMENTED / VERIFIED.** Tenant binding, workspace checks, authorization boundaries and safe fixture controls are enforced at the backend service/API boundary.

#### P12.3 — Test Run Lifecycle
**IMPLEMENTED / VERIFIED.** Durable queued/running/passed/failed/cancelled/expired lifecycle with row-lock concurrency protection. Expiration is available as an explicit authorized transition and as a background Celery Beat sweep using configurable timeout policy.

#### P12.4 — Evidence & Artifacts
**IMPLEMENTED / VERIFIED.** Structured results/evidence, runtime and migration identity, git SHA identity and tenant-scoped artifact references with SHA-256 metadata are persisted for completed runs.

#### P12.5 — Run History
**IMPLEMENTED / VERIFIED.** Tenant/workspace-scoped read-only history supports test, status and date filtering, bounded pagination and stable newest-first ordering. Active-run expiry uses a dedicated status/time index.

#### P12.6 — Exportable Verification Record
**IMPLEMENTED / VERIFIED.** Completed runs can produce immutable tenant-scoped verification snapshots with explicit engineering/product evidence boundaries and no claim of external acceptance.

#### Authorized UI
**IMPLEMENTED / VERIFIED.** Customer-facing Test Center UI is merged to `main` and consumes the authorized backend contracts for definitions, runs/history, artifacts and verification export.

### Phase 13 — Agent Teams & Marketplace
**BACKEND FOUNDATION IMPLEMENTED / UI NEXT.**

#### 13.1 — Team Definition Contract
**IMPLEMENTED.** Tenant-scoped TeamDefinition and immutable TeamVersion contracts.

#### 13.2 — Team Installation Boundary
**IMPLEMENTED.** Authorized tenant-local TeamInstallation with workspace scoping and audit coverage.

#### 13.3 — Team Execution Contract
**IMPLEMENTED.** Installed teams dispatch through the canonical WorkItem/Agent execution substrate.

#### 13.4 — Evaluation & Versioning
**IMPLEMENTED.** Immutable TeamEvaluation records tied to TeamVersion.

#### 13.5 — Marketplace Boundary
**IMPLEMENTED / BACKEND.** Publication/discovery plus authorized cross-tenant import. Public publications are imported as tenant-local TeamDefinition, TeamVersion and AgentDefinition copies; source publication provenance is retained on TeamInstallation. No AgentInstance is provisioned automatically.

#### 13.6 — Authorized UI
**NEXT.** Build authorized Team/Marketplace customer surfaces on the existing backend contracts.

#### 13.7 — End-to-End Product Acceptance
**PENDING.** Requires integration/runtime evidence for publish → discover → authorized import → local provisioning → WorkItem execution plus tenant/RBAC negative paths. Engineering evidence must remain distinct from external production/customer acceptance.

### Phase 14 — Scale, Governance & Production
**PLANNED.** Queue isolation, concurrency, routing, cost controls, SLOs, DR, security/compliance, regression prevention, incident response and external-production evidence.

## Phase 12 verification boundary

The Phase 12 engineering implementation is covered by repository CI, integration/unit tests and authorization/isolation checks. These are engineering evidence only. Local real-stack validation remains a separate evidence class, and external production/customer acceptance requires independent external evidence.

## Cross-cutting Definition of Done

Every phase must preserve:

- backend-enforced tenant isolation;
- RBAC at API/service boundaries;
- equivalent authorization controls for Human and Agent execution;
- policy-driven approval for risky actions;
- scoped tools and credentials;
- auditability;
- safe test execution;
- secrets excluded from source/artifacts;
- one authoritative Alembic graph;
- reproducible CI/release artifacts;
- explicit local/CI/production evidence boundaries.

## Immediate execution order

1. Merge and verify the Phase 13 marketplace import backend slice.
2. Build authorized Team/Marketplace UI against the existing backend contracts.
3. Add end-to-end publish → discover → import → tenant-local provisioning → execution evidence.
4. Keep external production/customer acceptance explicitly separate from repository/local evidence.
5. Continue workspace/runtime hardening and compatibility migration in parallel where safe.
