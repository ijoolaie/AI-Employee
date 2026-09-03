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

**Engineering implementation complete.** Phase 13 now includes:

1. tenant-scoped TeamDefinition and immutable TeamVersion;
2. authorized tenant-local TeamInstallation;
3. WorkItem-backed team execution;
4. immutable TeamEvaluation/version evidence;
5. Marketplace publication/discovery and authorized cross-tenant import;
6. tenant-local imported copies with source provenance and no automatic AgentInstance provisioning;
7. authorized Marketplace discovery and workspace-scoped installation review UI;
8. Playwright browser acceptance for authenticated discovery, review, installation UX and authorization-failure boundaries.

The Marketplace contract explicitly separates **install**, **customer acceptance** and **production deployment**. The repository does not claim external production/customer acceptance from CI or browser acceptance alone.

## Where the project is now

- V1.4: frozen architecture foundation.
- V1.5: active Agentic Operating Model extension.
- Phase 11 Unified Execution acceptance: **complete**.
- Phase 12 Test Center P12.1-P12.6: **implemented / operational hardening**.
- Phase 13 Agent Teams & Marketplace: **engineering complete**.
- Phase 14 Scale, Governance & Production: **next planned phase**.

## Evidence boundary

The repository distinguishes implementation evidence, automated/CI verification, local real-stack validation, external production evidence and Vendor/Reseller/Client acceptance. Green CI, a release or browser acceptance does not by itself prove external production deployment or customer acceptance.
