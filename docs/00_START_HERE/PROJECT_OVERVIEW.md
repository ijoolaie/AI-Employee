# Project Overview

## What this project is

AI Employee Platform is a **multi-tenant business operating platform** for Platform/Vendor, Reseller and Client organizations.

It is evolving from an Employee-centered implementation toward a **Human + Agent operating model**. Business work uses common execution contracts whether the executor is a Human, a specialized AI Agent, or a collaborative Human + Agent flow.

## Operating workspaces

```text
Platform / Vendor
        ↓
     Reseller
        ↓
      Client
```

Tenant, role and authorization boundaries prevent downstream workspaces from implicitly controlling upstream operations.

## Unified execution

Business work is represented through shared contracts for WorkItems and lifecycle, Human/Agent executors, authorization/RBAC, policy and approvals, scoped tools and credentials, audit/history, cancellation/retry and concurrency controls.

Existing Employee entities remain compatibility structures while execution capabilities migrate toward AgentDefinition, AgentInstance and WorkItem abstractions.

## Test Center

Phase 12 provides a first-class Test Center with tenant-scoped definitions and runs, workspace/RBAC enforcement, durable lifecycle and expiration, structured evidence, tenant-scoped artifacts, immutable verification export and authorized customer UI. Phase 12 is implemented through P12.6; runtime and external evidence remain separately classified.

## Phase 13 — Agent Teams & Marketplace

**Engineering implementation complete.** Phase 13 includes tenant-scoped TeamDefinition and immutable TeamVersion, authorized tenant-local TeamInstallation, WorkItem-backed team execution, immutable TeamEvaluation evidence, Marketplace publication/discovery/import, tenant-local copies with provenance, authorized Marketplace UI and Playwright browser acceptance.

The Marketplace contract explicitly separates **install**, **customer acceptance** and **production deployment**. The repository does not claim external production/customer acceptance from CI or browser acceptance alone.

## Phase 14 — Scale, Governance & Production

**Engineering workstreams 14.1–14.9 complete. Phase 14.10 external evidence pending.**

Completed engineering baselines cover:

- queue/worker isolation;
- concurrency and backpressure hardening;
- routing/scheduling;
- tenant-scoped cost controls;
- aggregate SLO/observability instrumentation;
- backup/restore and recovery procedures;
- security/compliance hardening and negative paths;
- regression/release gates;
- incident response and operational readiness.

Phase 14.10 remains external-only: an exact immutable release must be independently validated for deployment, live providers, measured SLO/DR, security/compliance, Vendor → Reseller → Client acceptance and rollback readiness.

## Where the project is now

- V1.4: frozen architecture foundation.
- V1.5: active Agentic Operating Model extension.
- Phase 11 Unified Execution acceptance: **complete**.
- Phase 12 Test Center P12.1-P12.6: **implemented / operational hardening**.
- Phase 13 Agent Teams & Marketplace: **engineering complete**.
- Phase 14.1–14.9: **engineering complete**.
- Phase 14.10 External Production / Customer Acceptance: **external-pending**.

## Evidence boundary

The repository distinguishes implementation evidence, automated/CI verification, local real-stack validation, external production evidence and Vendor/Reseller/Client acceptance. Green CI, a release or browser acceptance does not by itself prove external production deployment, measured production SLO attainment or customer acceptance.

## Active external gates

- #210 — consolidated immutable release / external-production gate;
- #19 — Vendor → Reseller → Client runtime isolation/RBAC evidence;
- #269 — Phase 14.10 evidence package and acceptance decision boundary.

These gates remain open until independent evidence is reconciled to one exact accepted release identity.
