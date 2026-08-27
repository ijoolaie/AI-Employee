# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

Authoritative delivery roadmap. V1.4 remains the frozen architecture foundation; V1.5 adds the Human + Agent operating model.

## Current position — 2026-08-27

**V1.4 frozen foundation + three-workspace separation + V1.5 Agentic Operating Model documented; implementation frontier is the unified Human/Agent execution layer.**

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

**🟡 DOCUMENTATION COMPLETE; NEXT IMPLEMENTATION PHASE.**

Build the common substrate before adding many new agent screens.

- WorkItem model and lifecycle
- AgentDefinition
- AgentInstance
- HumanExecutor
- unified execution service
- Human ↔ Agent delegation/fallback
- Agent ↔ Agent handoff
- policy-driven approvals
- scoped tools/credentials
- execution/audit timeline
- usage/cost attribution
- compatibility adapters for Employee APIs

**Gate:** the same WorkItem can be completed by Human or Agent with the same authorization and audit boundary.

## Phase 9 — Platform Command Center

**⚪ PLANNED.**

Role-specific experiences for Executive, Operations, Finance, HR, Sales, Marketing, Customer Success, Support, Security/Compliance, Engineering/QA and Analytics/BI.

Core surfaces: Command Center, Tenants, Agents, Agent Teams, Workflows, Tasks, Approvals, Knowledge, Memory, Tools/Integrations, Usage/Cost, Billing, Audit, Developer and **Test Center**.

Each business function must support Human, Agent and collaborative execution.

## Phase 10 — Reseller Operations Workspace

**⚪ PLANNED.**

Portfolio, Sales, Support, Operations, Billing and Customer Success optimized for reseller roles.

Specialized agents: Portfolio Health, Account Management, Sales, Support/Triage, Customer Success, Usage/Cost, Billing, Reporting and Operations.

Every task can be performed manually, delegated to an Agent, or collaboratively executed.

## Phase 11 — Client Business Workspace

**⚪ PLANNED.**

Outcome-first UI: Home, Customers, Orders, Products, Sales, Marketing, Support, Finance, Tasks, AI & Automation, Reports, Integrations and **Test Center**.

Specialized agents include Lead Research, Qualification, Outreach, Follow-up, Proposal, CRM, Marketing Content, SEO, Support, Order, Invoice/Finance, Document, Analytics and Reporting.

## Phase 12 — Test Center & Evidence Platform

**⚪ PLANNED.**

Test Center is a first-class dashboard tool in **Platform, Reseller and Client**, with role-aware visibility.

Required test families:

- API health
- authentication/session
- tenant isolation
- RBAC/permissions
- Agent smoke tests
- tool calls
- workflows
- Human ↔ Agent handoff
- approvals
- Knowledge/RAG
- memory
- integrations
- webhooks/idempotency
- usage metering
- billing/sandbox
- channels/notifications
- workers/queues
- model/provider
- full E2E business scenarios

Required UX: environment selector, dry-run/safe mode, production mutation guard, isolated test data, run history, logs, artifacts, pass/fail evidence and exportable verification records.

## Phase 13 — Agent Teams & Marketplace

**⚪ PLANNED.** Reusable Agent Teams, templates, agent versioning, evaluation suites, tenant-installed agents, marketplace boundary, long-running workflows, budgets, rate limits and SLA-aware orchestration.

Marketplace remains downstream of tenant isolation, RBAC, permission grants, usage and billing.

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

1. Finish/reconcile V1.4 workspace separation and CI.
2. Implement Phase 8 unified execution foundation.
3. Add Test Center contracts and backend authorization for all three workspaces.
4. Build Platform Command Center.
5. Build Reseller Operations Workspace.
6. Build Client Business Workspace.
7. Migrate existing Employee-backed capabilities through adapters.
8. Add Agent Teams/Marketplace only after the execution substrate is stable.
9. Execute Phase 6E production delivery independently; never confuse CI evidence with production evidence.
