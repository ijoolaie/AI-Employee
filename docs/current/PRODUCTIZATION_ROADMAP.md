# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

Authoritative delivery roadmap. V1.4 remains the frozen architecture foundation; V1.5 adds the Human + Agent operating model.

## Current position — 2026-08-30

**V1.4 frozen foundation + V1.5 Agentic Operating Model. Unified Execution implementation and lifecycle/concurrency hardening, Platform/Reseller implementation slices, and role-aware workspace separation are merged. Production Certification run 33322632204 passed the real-stack Unified WorkItem Human gate; the active frontier is reconciliation of the remaining Unified Execution exit criteria, runtime workspace verification, and production hardening.**

The product is **Agent-first, not Employee-first**. Every capability in Platform, Reseller and Client must be executable by a Human, a specialized Agent, or both. The same WorkItem, authorization, tools, approvals, audit and output contracts apply to either executor. Existing Employee code remains a compatibility layer during migration.

Authoritative V1.5 architecture: `docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`.

## Phase 0 — Release Integrity

**🟢 COMPLETE.** Immutable release identity, certification boundaries and release evidence are established.

## Phase 1 — Vendor Edition

**🟢 FOUNDATION IMPLEMENTED.** Vendor runtime, provisioning, entitlement, licensing and audit boundaries exist; operational authority/tooling continues.

## Phase 2 — Reseller Edition

**🟢 FOUNDATION IMPLEMENTED.** Reseller identity, isolation, lifecycle, quota delegation, licensing, audit and support boundaries exist. V1.5 adds agentic portfolio/revenue operations.

## Phase 3 — Client Edition

**🟢 FOUNDATION IMPLEMENTED.** Client isolation, RBAC, lifecycle and audit boundaries exist. V1.5 adds business-outcome-oriented Human/Agent execution.

## Phase 4 — Delivery Package

**🟢 IMPLEMENTED / LOCAL VALIDATION COMPLETE.** Release, configuration, installation, migration, recovery, security and handoff artifacts exist.

## Phase 5 — Commercial Production

**🟡 SUBSTANTIALLY IMPLEMENTED.** External payment, deployment, monitoring, rollback/recovery and environment-specific certification remain open.

## Phase 6 — Edition-Separated Delivery

**🟢 6A–6D COMPLETE; 6E OPEN FOR EXTERNAL EXECUTION.** Vendor → Reseller → Client delivery remains one authoritative source with environment-specific evidence required.

## Phase 7 — Existing Invoice Capability

**🟢 IMPLEMENTED / LOCAL VERIFIED.** Existing invoice functionality remains supported and must migrate toward the unified WorkItem/Agent model when changed. Do not duplicate the Stripe billing path.

# V1.4 — Architecture & Gap Closure

**🟡 FROZEN BASELINE / IMPLEMENTATION TRACK.** Tenant/worker context, knowledge isolation, conversation isolation, scoped API keys and idempotent usage work were established in the first dependency-ordered wave. V1.4 security, tenant, RBAC, billing and migration invariants remain mandatory for V1.5.

# V1.5 — Agentic Productization Roadmap

## Phase 8 — Unified Execution Foundation

**🟢 IMPLEMENTATION SUBSTANTIALLY COMPLETE / E2E ACCEPTANCE NEAR COMPLETION.** Merged implementation slices cover WorkItem execution, delegation/handoff, policy/tool controls, telemetry, Test Center contracts, Workspace projections, and Agent Team orchestration/lifecycle/recovery/completion/health. Lifecycle and dispatch concurrency hardening are also merged. Remaining work is final runtime acceptance, reconciliation, gap closure and production hardening—not initial implementation of the execution substrate.

## Phase 9 — Platform Command Center

**🟢 IMPLEMENTATION SLICES MERGED.** Role-specific Platform experiences and core operational surfaces are implemented; remaining acceptance is tied to real execution integration and evidence.

## Phase 10 — Reseller Operations Workspace

**🟢 IMPLEMENTATION SLICES + ROLE-AWARE WORKSPACE MERGED.** Portfolio, Sales, Support, Operations, Billing and Customer Success surfaces are implemented; remaining acceptance is tied to real execution integration and evidence.

## Phase 11 — Client Business Workspace / Unified Execution Acceptance

**🟡 ACCEPTANCE RECONCILIATION IN PROGRESS.** Workspace architecture and the major execution/lifecycle slices are merged. Production Certification run 33322632204 passed with Failed gates: 0 and included the real-stack Human WorkItem assignment → dispatch → PostgreSQL state → audit/history gate. The remaining acceptance scope is explicit reconciliation of Agent runtime, approval/policy negatives and real workspace API usage against Issue #170. Issue #170 remains open until all exit criteria are evidenced and reconciled.

## Phase 12 — Test Center & Evidence Platform

**⚪ PLANNED.** First-class role-aware Test Center with safe execution, isolated data, run history, logs, artifacts, pass/fail evidence and exportable verification records.

## Phase 13 — Agent Teams & Marketplace

**⚪ PLANNED.** Reusable Agent Teams, templates, agent versioning, evaluation suites, tenant-installed agents, marketplace boundary, long-running workflows, budgets, rate limits and SLA-aware orchestration.

## Phase 14 — Scale, Governance & Production

**⚪ PLANNED.** Queue isolation, concurrency, model routing, cost controls, SLOs, disaster recovery, security/compliance, evaluation/regression prevention, incident response, retention/deletion, explainability, audit and external-production evidence.

# Cross-cutting Definition of Done

Every phase must preserve:

- backend-enforced tenant isolation
- RBAC at API/service boundaries
- equal authorization for Human and Agent execution
- policy-driven approval for risky actions
- scoped tools and credentials
- complete auditability
- usage/cost attribution
- safe test execution
- secrets excluded from source/artifacts
- one authoritative Alembic graph
- reproducible CI/release artifacts
- explicit local/CI/production evidence boundaries

# Immediate execution order

1. Reconcile Production Certification run 33322632204 and existing acceptance evidence against every Issue #170 exit criterion; add only genuinely missing Human/Agent, approval/policy or workspace real-API evidence, then close #170.
2. Verify Platform/Reseller/Client workspace actions against real WorkItem and Agent APIs, including role and tenant boundaries.
3. Close runtime gaps discovered by E2E acceptance and preserve authorization, tenant isolation and audit invariants.
4. Expand Test Center evidence where repeatable acceptance proof is required.
5. Continue compatibility migration for existing Employee-backed capabilities.
6. Continue production hardening and independently collect external production evidence; do not treat CI as production certification.
7. Execute Phase 6E Vendor → Reseller → Client production delivery when the required external evidence is available.
8. Add downstream Agent Teams/Marketplace and scale/governance work only after the execution substrate and acceptance are operationally stable.
