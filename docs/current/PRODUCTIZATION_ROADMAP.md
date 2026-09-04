# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-04

V1.4 remains the frozen architecture foundation. V1.5 is the active Human + Agent operating-model extension.

Phase 11 Unified Execution acceptance is complete. Phase 12 Test Center & Evidence Platform is implemented through P12.6, including authorized UI and stale-run expiration hardening. Phase 13 Agent Teams & Marketplace engineering implementation is complete through authorized UI and deterministic browser acceptance. Phase 14 engineering workstreams 14.1–14.9 are complete; Phase 14.10 is the only remaining external-evidence gate.

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
**IMPLEMENTED / VERIFIED.** Durable lifecycle with concurrency protection and stale-run expiration.

#### P12.4 — Evidence & Artifacts
**IMPLEMENTED / VERIFIED.** Structured results/evidence, runtime and migration identity, git SHA identity and tenant-scoped artifact references are persisted for completed runs.

#### P12.5 — Run History
**IMPLEMENTED / VERIFIED.** Tenant/workspace-scoped history supports filtering, bounded pagination and stable ordering.

#### P12.6 — Exportable Verification Record
**IMPLEMENTED / VERIFIED.** Completed runs can produce immutable tenant-scoped verification snapshots with explicit evidence boundaries.

#### Authorized UI
**IMPLEMENTED / VERIFIED.** Customer-facing Test Center UI is merged to `main`.

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
**IMPLEMENTED / BACKEND.** Publication/discovery plus authorized cross-tenant import with tenant-local copies and provenance. No AgentInstance is provisioned automatically.

#### 13.6 — Authorized UI
**IMPLEMENTED / MERGED.** Authenticated Marketplace discovery, workspace-scoped install review, tenant-local result/provenance and explicit install/acceptance/deployment boundary messaging.

#### 13.7 — End-to-End Product Acceptance
**IMPLEMENTED / MERGED.** Playwright acceptance covers authenticated discovery, workspace-scoped review, deterministic installation UX and authorization failure handling. Browser acceptance does not claim a live production cross-tenant environment.

### Phase 14 — Scale, Governance & Production
**ENGINEERING 14.1–14.9 COMPLETE / 14.10 EXTERNAL-PENDING.**

#### 14.1 — Queue / Worker Isolation
**IMPLEMENTED / MERGED.** Explicit Celery queue topology and worker separation.

#### 14.2 — Concurrency, Backpressure & Fairness
**IMPLEMENTED / MERGED.** Bounded prefetch, late acknowledgement, worker-loss redelivery and worker recycling baseline. This is not a full tenant-fairness scheduler.

#### 14.3 — Routing & Scheduling
**IMPLEMENTED / MERGED.** Centralized schedule cadence and routing regression coverage.

#### 14.4 — Cost & Usage Controls
**IMPLEMENTED / MERGED.** Tenant-scoped usage cost-limit enforcement primitive and regression coverage.

#### 14.5 — SLO, Reliability & Observability
**IMPLEMENTED / MERGED.** Aggregate-only SLO outcome/error-budget instrumentation. Production attainment remains deployment evidence.

#### 14.6 — Disaster Recovery / Backup & Restore
**IMPLEMENTED / MERGED.** Reproducible backup/verification/isolated-restore scripts and recovery baseline with planning RPO/RTO thresholds. Production RPO/RTO remains external evidence.

#### 14.7 — Security & Compliance Hardening
**IMPLEMENTED / MERGED.** Marketplace import collision hardening, secret-bearing policy rejection and negative-path coverage. This is engineering hardening, not external compliance certification.

#### 14.8 — Regression & Release Gates
**IMPLEMENTED / MERGED.** CI source-level contract coverage for workflow applicability, migrations, backend/frontend regression, exact release identity, checksums and edition artifact source identity.

#### 14.9 — Incident Response & Operational Readiness
**IMPLEMENTED ENGINEERING BASELINE / MERGED.** Incident taxonomy, severity model, ownership boundaries, actionable response/rollback/recovery flow, sanitized evidence capture and exercise requirements are documented and contract-validated in CI. No real incident or production-response claim is implied.

#### 14.10 — External Production Certification & Customer Acceptance Evidence
**EXTERNAL-PENDING.** The final gate requires one exact immutable release identity plus independent deployment, provider, SLO, DR, security/compliance, Vendor → Reseller → Client acceptance and rollback evidence. CI/repository evidence alone cannot close this gate.

## Evidence boundary

Engineering implementation, CI, CodeQL, Architecture Guard, operational workflow results and local runtime evidence are distinct from external production evidence. None of them alone establishes live deployment, live third-party provider validation, measured production SLO attainment, customer acceptance, commercial go-live or independent certification.

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

1. Preserve completed Phase 13 and Phase 14.1–14.9 engineering evidence.
2. Maintain the Phase 14.10 external evidence gate.
3. Build a fresh immutable production candidate from the intended current mainline only when an external target exists.
4. Reconcile deployment, artifacts, migrations, provider validation, measured SLO/DR evidence and Vendor → Reseller → Client acceptance to that exact candidate.
5. Do not claim commercial production readiness until the independent evidence package is accepted.
