# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-09-10

This roadmap uses three independent axes and must not mix them:

- **Release:** the currently certified release candidate is `v1.3.8` at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- **Architecture:** `V1.5 Agentic Operating Model` is the active architecture baseline. It is **not** a separately certified release.
- **Engineering:** the current mainline is `decde0ad333ba972a79053b3da6489f92a2648de` and is **not certified**.

The roadmap therefore does not treat V1.5 or the current mainline as a release. Certification remains bound to the exact release SHA.

## Current position

Phase 11 Unified Execution acceptance is complete. Phase 12 Test Center is implemented with operational hardening. Phase 13 Agent Teams & Marketplace engineering is complete. Phase 14.1–14.16 engineering is complete for the tracked implementation.

The application/product engineering frontier has crossed into **governance hardening, concurrency/idempotency hardening and production-certification preparation**. Stage 7 remains the active external program stage. Stage 8 workforce governance engineering is active on mainline.

### Governance hardening checkpoint — Stage 8 implementation

The governed workforce foundation has been implemented through controlled PRs:

- PR #374 — kill-switch enforcement at WorkItem admission.
- PR #375 — PostgreSQL-serialized AgentInstance concurrency admission.
- PR #376 — direct AgentInstance activation bypass blocked.
- PR #378 — governance fingerprint freshness at activation.
- PR #379 — Access Review freshness at activation.
- PR #380 — Access Review reactivation bypass blocked.
- PR #381 — Access Review freshness enforced at execution.
- PR #382 — latest Access Review decision required at execution.
- PR #383 — delegation freshness enforced at execution.
- PR #384 — governance authority fingerprint enforced at execution.

### Post-release reliability hardening checkpoint

After `v1.3.8`, mainline reliability work closed multiple real race windows through controlled PRs:

- PR #398 — Stripe Customer idempotency boundary.
- PR #401 — Subscription initialization race recovery.
- PR #403 — durable Stripe Customer reconciliation.
- PR #404 — Shopify webhook registration serialization.
- PR #405 — Shopify sync serialization.
- PR #406 — PaymentRefund and Shopify webhook delivery race hardening.
- PR #408 — customer upsert race hardening.
- PR #409 — Stripe Customer identity-resolution serialization.
- PR #411 — OnboardingProgress creation race recovery.
- PR #413 — transactional outbox enqueue race recovery.
- PR #415 — tenant registration and RBAC permission creation race hardening.
- PR #417 — refund lifecycle BillingEvent race recovery.
- PR #419 — BillingEvent `record_event()` race recovery.
- PR #421 — concurrent RAG indexing serialization.

The current engineering frontier is PR #423 / Issue #422, which closes a real PostgreSQL NULL-uniqueness gap for TeamInstallation scopes. It is open and must pass the normal required gates before merge.

These post-release changes are engineering evidence only. They do not transfer `v1.3.8` certification.

## Stage 1–6 — completed engineering foundations

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

PR #312 merged at `7657b4244a47af95960e5854fa52f92a0dbe618b`. The tenant-scoped workspace read model combines WorkItems, pending workflow/tool approvals and Human/Agent executor queue counts while preserving authorization and mutation boundaries.

## Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Stage 7 remains the active external program stage because production acceptance requires evidence from a real external target. Engineering hardening may proceed in parallel but never transfers the certified release identity.

| Priority | Work package | Class | Status / exit evidence |
|---|---|---|---|
| P0 | 7.1 Immutable release & release identity | MIXED | `v1.3.8` frozen; newer mainline requires a new release identity |
| P0 | 7.2 External production infrastructure deployment | EXTERNAL | **PENDING real infrastructure** |
| P0 | 7.3 Real backup/restore & disaster-recovery drill | EXTERNAL | PENDING target evidence |
| P0 | 7.4 Production SLO, SLIs & error budget | MIXED | PENDING measured target evidence |
| P0 | 7.5 Live provider integration validation | EXTERNAL | PENDING live providers |
| P0 | 7.6 Vendor → Reseller → Client runtime isolation/RBAC certification | EXTERNAL | PENDING real-stack actor evidence |
| P0 | 7.7 Dynamic application security testing (DAST) | MIXED | PENDING deployed target |
| P0 | 7.8 Independent penetration test / security review | EXTERNAL | PENDING independent review |
| P0 | 7.9 Production networking hardening | MIXED | PENDING target perimeter evidence |
| P0 | 7.10 Secret management, rotation & recovery | MIXED | PENDING external lifecycle evidence |
| P0 | 7.11 High availability & failure-recovery rehearsal | MIXED | PENDING target rehearsal |
| P0 | 7.12 Incident-response drill | MIXED | PENDING live drill |
| P0 | 7.13 Alert ownership & on-call escalation | MIXED | PENDING staffed operational evidence |
| P0 | 7.14 Final external certification & customer acceptance | EXTERNAL | PENDING #210/#269 |
| P1 | 7.15 Data retention & lifecycle enforcement | MIXED | Engineering implemented; target verification pending |
| P1 | 7.16 Human-in-the-loop reconciliation | ENGINEERING | Reconciled |
| P1 | 7.17 Documentation consolidation & evidence index | ENGINEERING | **Current-main reconciliation in progress; this pass updates canonical status/manifest/roadmap/gap truth** |
| P1 | 7.18 Platform operations dashboard | ENGINEERING | Implemented |
| P1 | 7.19 Customer usage, budget & cost controls | MIXED | Engineering implemented; target validation pending |
| P1 | 7.20 Cost anomaly detection & forecasting | ENGINEERING | Implemented |

### Stage 7 sequencing rule

P0 items are release/certification blockers. P1 items are productization/operational completeness items. No P0 external gate may be represented as complete from repository evidence alone. Customer acceptance cannot be declared while required P0 evidence is missing.

## Stage 8 — AI Company Operating Model Foundation
**Class: PRODUCT / ARCHITECTURE — ENGINEERING ACTIVE / NOT A RELEASE**

Stage 8 is an active engineering workstream. The governed workforce foundation is present on mainline, while the stage remains open until the remaining execution-boundary audit, workforce product surfaces, evaluation gates and release evidence are complete.

### 8.1 Workforce governance model
Define the organization-level model on top of V1.5:

- Human Owner / CEO / Chairman as final authority.
- AI Board as advisory/governance layer.
- AI Chief of Staff and AI Internal Manager as executive operating layer.
- Explicit decision rights, approval thresholds and escalation paths.
- Auditability of every organizational decision and delegation.

**Engineering checkpoint:** AgentInstance lifecycle controls, Access Review freshness, delegation freshness and execution-time authority fingerprinting are implemented on mainline. Remaining work is systematic coverage of every execution/side-effect boundary.

### 8.2 Founding AI workforce
Create the initial first-party workforce as reusable role definitions and customer-facing templates. The detailed role catalog is maintained in `docs/blueprint/AI_COMPANY_FOUNDING_WORKFORCE.md`.

Initial active candidates include:

- AI Chief of Staff / Coordinator
- AI Internal Manager
- AI Strategy Advisor
- AI Technology Advisor / CTO
- AI Software Developer
- AI QA Engineer
- AI DevOps / Infrastructure Engineer
- AI Network / Security Engineer
- AI CISO / Security Manager
- AI Finance / Accountant
- AI Legal & Compliance Advisor
- AI Marketing Manager
- AI SEO Specialist
- AI Content Writer
- AI Graphic Designer
- AI Sales Manager
- AI Customer Success / Support Manager
- AI Data & Analytics Specialist
- AI Knowledge Manager
- AI Corporate Secretary

The broader catalog may keep specialized roles dormant as marketplace templates until justified by workload or customer demand.

### 8.3 Workforce lifecycle
Formalize:

`Need → Proposal → Board Review → CEO Approval → Existing Template or New Role → Evaluation → Publication → Installation → AgentInstance → Active → Suspend/Retire`

No autonomous role creation may bypass policy, evaluation or CEO authority.

### 8.4 Customer workforce marketplace
Expose the same role definitions as installable customer templates, while keeping:

`AgentDefinition ≠ AgentTemplate ≠ AgentInstance`

Templates are reusable products; instances are tenant-scoped deployments with their own configuration, permissions, credential references, memory, usage and run history.

### 8.5 Team compositions
Define reusable teams such as Marketing, Software, Security, Finance and Operations teams. Team composition must remain policy-governed and tenant-scoped.

### 8.6 AI Company governance UX
Add organization-level views for Board decisions, workforce roster, agent/team health, pending approvals, delegation and handoffs, cost/usage by employee/team, workforce proposals, agent registry/lifecycle, security/risk status and audit trail.

### 8.7 Engineering execution plan
The Stage 8 design is decomposed into domain entities, lifecycle state machine, identity/RBAC, per-action tool authorization, agent-to-agent trust, approval engine, workforce orchestration, evaluation gates, memory isolation, usage/cost budgets, audit events, APIs, UI surfaces, security/E2E tests and final release evidence.

Canonical execution plan: `docs/blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md`.

**Next Stage 8 engineering gate:** complete the execution and side-effect boundary audit, including runtime adapters, tool execution, WorkItem/run transitions, credential use, external side effects and mutable authority surfaces. Only after that audit should the post-`v1.3.8` mainline be promoted into a new release candidate.

## Stage 9 — Autonomous Workforce Optimization
**Class: PRODUCT / RESEARCH — future**

After Stage 8 is operational, the platform may introduce controlled optimization:

- workload balancing;
- capability-based routing;
- model selection by task/risk/cost;
- agent performance evaluation;
- version fitness and rollback;
- workforce capacity planning;
- controlled proposals for new roles and team restructuring.

Human governance remains above autonomous optimization.

## Stage 10 — AI Company Operating System
**Class: LONG-TERM PRODUCT VISION — future**

The long-term product direction is an AI Company Operating System: a multi-tenant platform in which humans define authority and accountability while specialized agents execute governed business work.

Potential capabilities include organization-wide command center, constitutional/policy layer, autonomous but interruptible workflows, agent/version registry, workforce analytics, cross-team orchestration, commercial template marketplace and tenant-safe autonomous operations.

Stage 10 is a product vision, not a current implementation claim.

## Cross-cutting Definition of Done

Every stage and work package must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditable agent identity, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation before closure.

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, bounded synthetic load, local RBAC acceptance and simulated providers are engineering/release evidence only. They do not substitute for live production deployment, live provider evidence, measured production SLO/DR, independent security/compliance review or customer acceptance.

Certification never transfers automatically across SHAs.

The canonical gap register is `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`.
