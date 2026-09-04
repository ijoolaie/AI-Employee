# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-03

V1.4 remains the frozen architecture foundation. V1.5 is the active Human + Agent operating-model extension.

Phase 11 Unified Execution acceptance is complete. Phase 12 Test Center & Evidence Platform is implemented through P12.6, including the authorized customer UI and automatic stale-run expiration sweep. Phase 13 Agent Teams & Marketplace engineering implementation is now complete through authorized UI and deterministic browser acceptance; external production/customer acceptance remains a separate evidence class.

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
**ENGINEERING IMPLEMENTATION COMPLETE / EXTERNAL ACCEPTANCE PENDING.**

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
**IMPLEMENTED / MERGED.** Authenticated Marketplace discovery, workspace-scoped install review, tenant-local result/provenance and explicit install/acceptance/deployment boundary messaging are covered.

#### 13.7 — End-to-End Product Acceptance
**IMPLEMENTED / MERGED.** Playwright acceptance covers authenticated discovery, workspace-scoped review, deterministic install success UX and authorization failure handling. Backend authorization and tenant isolation remain authoritative; the browser suite does not claim a live production cross-tenant environment.

### Phase 14 — Scale, Governance & Production
**IN PROGRESS.** Queue isolation, concurrency, routing, cost controls, SLOs, DR, security/compliance, regression prevention, incident response and external-production evidence.

#### 14.1 — Queue / Worker Isolation
**IMPLEMENTED / MERGED.** Explicit Celery queue topology and worker separation.

#### 14.2 — Concurrency, Backpressure & Fairness
**IMPLEMENTED / MERGED.** Bounded prefetch, late acknowledgement, worker-loss redelivery and worker recycling baseline.

#### 14.3 — Routing & Scheduling
**IMPLEMENTED / MERGED.** Centralized schedule cadence and routing regression coverage.

#### 14.4 — Cost & Usage Controls
**IMPLEMENTED / MERGED.** Tenant-scoped usage cost-limit enforcement primitive and regression coverage.

#### 14.5 — SLO, Reliability & Observability
**IMPLEMENTED / MERGED.** Aggregate-only SLO outcome/error-budget instrumentation; production attainment remains deployment evidence.

#### 14.6 — Disaster Recovery / Backup & Restore
**IMPLEMENTED / MERGED.** Reproducible backup/verification/isolated-restore scripts and recovery baseline with explicit planning RPO/RTO thresholds.

#### 14.7 — Security & Compliance Hardening
**IMPLEMENTED / MERGED.** Marketplace import hardening prevents cross-workspace slug collisions and rejects secret-bearing policy fields; negative-path tests and evidence boundaries are recorded. This is engineering hardening, not external compliance certification.

#### 14.8 — Regression & Release Gates
**IMPLEMENTED BASELINE / IN PROGRESS.** CI now includes a source-level contract check covering workflow applicability, migration validation, targeted backend/frontend regression, exact release-ref checkout, release commit identity, package checksum verification and edition artifact source identity. The gate is evidence for repository/release-process correctness; it does not by itself establish production certification.

## Evidence boundary

Phase 13 completion is an engineering/repository milestone. CI, CodeQL, Architecture Guard and applicable operational workflow results are engineering evidence; prior local Docker validation is local/runtime evidence. None of these records alone establishes external production deployment, live third-party provider validation, customer acceptance, commercial go-live or production certification.

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

1. Phase 13 engineering implementation is complete and recorded.
2. Continue Phase 14 scale, governance and production-hardening work.
3. Preserve explicit separation between repository/local engineering evidence and external production/customer acceptance.
4. Continue workspace/runtime hardening and compatibility migration in parallel where safe.
