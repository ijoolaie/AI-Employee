# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-09-12

This roadmap keeps three independent axes separate:

- **Release:** latest exact-SHA certified release candidate is `v1.4.0-rc.4` at `4cadd2df003d72de43546466a47e2c66062002c6`, certified by Production Certification Run `34693535048`.
- **Architecture:** `V1.5 Agentic Operating Model` remains the active architecture baseline. It is not itself a release identity.
- **Engineering phase:** Phase 11–14.x and Stage 8 describe implementation/evidence maturity; phase completion does not create a release automatically.

Documentation reconciliation commits landed after the certified candidate SHA. Therefore the current mainline is not implicitly certified; a final release SHA must be frozen and certified again before promotion.

## Current position

Phase 11 Unified Execution acceptance is complete. Phase 12 Test Center is implemented with operational hardening. Phase 13 Agent Teams & Marketplace engineering is complete. Phase 14.1–14.16 tracked engineering work is complete/reconciled.

The execution-boundary hardening sequence through PR #499 is reconciled. The immediate program frontier is now **P0 external production execution and certification**, with Stage 8 workforce governance continuing as a separate engineering/product track.

### Latest execution-boundary checkpoint

Key merged hardening includes:

- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through outbox.
- PR #466 — atomic Run creation/outbox failure boundary hardened with nested savepoint.
- PR #467 — WorkItem cancellation fenced at the DB boundary.
- PR #468 — workflow replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed.
- PR #473 — workflow re-entry after child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced.
- PR #477 — workflow terminal states made immutable.
- PR #479 — post-timeout/terminal workflow advancement fenced.
- PR #482 — durable WorkflowRun execution lease, heartbeat, ownership fencing and bounded recovery.
- PR #486 — durable parallel-branch execution lease/recovery and optimistic ownership fencing.
- PR #487 — concurrent Run execution admission serialized with a database row lock.
- PR #499 — SQLAlchemy workflow child-identity FK DDL cycle warning eliminated with `use_alter=True`, without weakening FK integrity or changing durable child-run identity semantics.

## Stage 1–6 — completed engineering foundations

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — ENGINEERING COMPLETE / RECONCILED**

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / RECONCILED**

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — ENGINEERING COMPLETE / RECONCILED**

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — ENGINEERING COMPLETE / RECONCILED**

## Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Stage 7 is the active external program stage. The repository has an exact-SHA certified candidate, but there is still no verified external deployment of that candidate.

| Priority | Work package | Class | Status / exit evidence |
|---|---|---|---|
| P0 | 7.1 Immutable release & release identity | MIXED | `v1.4.0-rc.4` certified at exact SHA; final release freeze pending |
| P0 | 7.2 External production infrastructure deployment | EXTERNAL | **PENDING real infrastructure** |
| P0 | 7.3 Real backup/restore & disaster recovery | EXTERNAL | PENDING target evidence and measured RPO/RTO |
| P0 | 7.4 Production SLO, SLIs & error budget | MIXED | Engineering contract complete; measured target evidence pending |
| P0 | 7.5 Live provider integration validation | EXTERNAL | PENDING live providers |
| P0 | 7.6 Vendor → Reseller → Client runtime isolation/RBAC | EXTERNAL | CI gate complete; external actor evidence pending |
| P0 | 7.7 Dynamic application security testing (DAST) | MIXED | CI baseline complete; deployed authenticated scan pending |
| P0 | 7.8 Independent penetration test / security review | EXTERNAL | PENDING independent review |
| P0 | 7.9 Production networking hardening | MIXED | Engineering contract complete; target perimeter evidence pending |
| P0 | 7.10 Secret management, rotation & recovery | MIXED | Engineering contract complete; target lifecycle evidence pending |
| P0 | 7.11 High availability & failure recovery | MIXED | Engineering rehearsal complete; target rehearsal pending |
| P0 | 7.12 Incident-response drill | MIXED | Engineering simulation complete; live drill pending |
| P0 | 7.13 Alert ownership & on-call escalation | MIXED | Routing contract complete; live paging evidence pending |
| P0 | 7.14 Final external certification & customer acceptance | EXTERNAL | Pending #210/#269 |
| P1 | 7.15 Data retention & lifecycle enforcement | MIXED | Engineering implemented; target verification pending |
| P1 | 7.16 Human-in-the-loop reconciliation | ENGINEERING | Complete |
| P1 | 7.17 Documentation consolidation & evidence index | ENGINEERING | Reconciled 2026-09-12 |
| P1 | 7.18 Platform operations dashboard | ENGINEERING | Implemented |
| P1 | 7.19 Customer usage, budget & cost controls | MIXED | Engineering implemented; target validation pending |
| P1 | 7.20 Cost anomaly detection & forecasting | ENGINEERING | Implemented |

### Stage 7 sequencing rule

P0 items are release/certification blockers. No P0 external gate may be represented as complete from repository evidence alone. All external records must bind to one exact immutable release SHA/tag and its artifact identity. Customer acceptance cannot be declared while required P0 evidence is missing.

## Stage 8 — AI Company Operating Model Foundation
**Class: PRODUCT / ARCHITECTURE — ENGINEERING ACTIVE / NOT A RELEASE**

The governed workforce foundation is implemented on mainline. The active engineering gate is systematic enforcement across execution and side-effect boundaries, including runtime adapters, tool execution, WorkItem/Run transitions, credential use, external side effects and mutable authority surfaces.

The Stage 8 model preserves:

- Human Owner / CEO / Chairman as final authority.
- AI Board as advisory/governance layer.
- AI Chief of Staff and AI Internal Manager as executive operating layer.
- Governed AgentInstance lifecycle and Access Review freshness.
- Delegation freshness and execution-time authority fingerprinting.
- Tenant-scoped templates/instances and auditable decisions.

Canonical execution plan: `docs/blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md`.

Stage 8 remains an engineering/product track and must not be mislabeled as a new release until implementation and release policy establish the release identity.

## Stage 9 — Autonomous Workforce Optimization
**Class: PRODUCT / RESEARCH — FUTURE**

Controlled workload balancing, capability routing, model selection by task/risk/cost, agent evaluation, version fitness/rollback and workforce capacity planning may follow once Stage 8 is operational. Human governance remains above autonomous optimization.

## Stage 10 — AI Company Operating System
**Class: LONG-TERM PRODUCT VISION — FUTURE**

The long-term direction is an AI Company Operating System with organization-wide command, policy, governed autonomous workflows, agent/version registry, workforce analytics, cross-team orchestration and tenant-safe operations. This is a product vision, not a current implementation claim.

## Cross-cutting Definition of Done

Every stage must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditable agent identity, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation before closure.

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, synthetic load, local RBAC acceptance and simulated providers are engineering/release evidence only. They do not substitute for live production deployment, live provider evidence, measured production SLO/DR, independent security/compliance review or customer acceptance.

Certification never transfers automatically across SHAs.

Canonical companion records:
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/00_START_HERE/CURRENT_PRIORITIES.md`
- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`
- `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/releases/RELEASE_TRUTH_LEDGER.md`
