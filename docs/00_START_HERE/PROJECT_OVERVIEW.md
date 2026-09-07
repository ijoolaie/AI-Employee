# Project Overview

## What this project is

AI Employee Platform is a **multi-tenant business operating platform** for Platform/Vendor, Reseller and Client organizations.

It is evolving from an Employee-centered implementation toward a **Human + Agent operating model**. Business work uses common execution contracts whether the executor is a Human, a specialized AI Agent, or a collaborative Human + Agent flow.

## Versioning model

The repository uses three independent version axes. They must not be treated as the same thing.

| Axis | Meaning | Current truth |
|---|---|---|
| Release | Immutable product snapshot tied to an exact Git tag/SHA | `v1.3.8` / `fd1e74b6...` certified |
| Architecture | Platform architecture and operating-model generation | V1.5 Agentic Operating Model |
| Engineering phase | Delivery workstream / acceptance gate | Phase 14.1–14.9 complete; 14.10 external-pending |

V1.5 is an **architecture/documentation baseline**, not a separately certified product release. Phase completion is engineering evidence, not release certification.

Canonical rules: `docs/00_START_HERE/VERSIONING_TRUTH.md`.

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

Existing Employee entities remain compatibility structures while the architecture migrates toward AgentDefinition, AgentInstance and WorkItem abstractions.

## Architecture status

- **V1.4:** frozen architecture foundation.
- **V1.5:** Human + Agent / Agentic Operating Model extension.

The V1.5 blueprint defines the target execution model and security/governance contracts. It does not, by itself, certify every named capability as implemented.

## Engineering status

### Phase 12 — Test Center

**Implemented / operational hardening.** Phase 12 provides tenant-scoped definitions and runs, workspace/RBAC enforcement, durable lifecycle and expiration, structured evidence, tenant-scoped artifacts, immutable verification export and authorized customer UI. Runtime and external evidence remain separately classified.

### Phase 13 — Agent Teams & Marketplace

**Engineering implementation complete.** Phase 13 includes tenant-scoped TeamDefinition and immutable TeamVersion, authorized tenant-local TeamInstallation, WorkItem-backed team execution, immutable TeamEvaluation evidence, Marketplace publication/discovery/import, tenant-local copies with provenance, authorized Marketplace UI and Playwright browser acceptance.

The Marketplace contract explicitly separates **install**, **customer acceptance** and **production deployment**.

### Phase 14 — Scale, Governance & Production

**Engineering workstreams 14.1–14.9 complete. Phase 14.10 external evidence pending.**

Completed engineering baselines cover queue/worker isolation, concurrency and backpressure hardening, routing/scheduling, tenant-scoped cost controls, aggregate SLO/observability instrumentation, backup/restore and recovery procedures, security/compliance hardening, regression/release gates, incident response and operational readiness.

Phase 14.10 remains external-only: an exact immutable release must be independently validated for deployment, live providers, measured SLO/DR, security/compliance, Vendor → Reseller → Client acceptance and rollback readiness.

## Current release truth

- Certified release candidate: **`v1.3.8`**.
- Certified commit: **`fd1e74b6b4c1701f7443efc202bad161ff19618c`**.
- Certification run: **`34052885700` — PASS**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance / live provider validation: **PENDING**.

## Where the project is now

```text
RELEASE
v1.3.8 (certified candidate)
        │
        │ exact release identity
        ▼
ARCHITECTURE
V1.4 frozen foundation
        │
        ▼
V1.5 Agentic Operating Model
        │
        ▼
ENGINEERING
Phase 11 → 12 → 13 → 14
        │
        ▼
NEXT CERTIFIED RELEASE
(to be created only after release gates pass)
```

This sequence is intentional: architecture and engineering may advance while the latest certified release remains v1.3.8.

## Evidence boundary

The repository distinguishes implementation evidence, automated/CI verification, local real-stack validation, external production evidence and Vendor/Reseller/Client acceptance. Green CI, a release or browser acceptance does not by itself prove external production deployment, measured production SLO attainment or customer acceptance.

## Active external gates

- #210 — consolidated immutable release / external-production gate;
- #19 — Vendor → Reseller → Client runtime isolation/RBAC evidence;
- #269 — Phase 14.10 evidence package and acceptance decision boundary.

These gates remain open until independent evidence is reconciled to one exact accepted release identity.
