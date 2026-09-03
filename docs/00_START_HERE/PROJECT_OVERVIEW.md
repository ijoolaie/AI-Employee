# Project Overview

## What this project is

AI Employee Platform is a **multi-tenant business operating platform** for Platform/Vendor, Reseller and Client organizations.

It is evolving from an Employee-centered implementation toward a **Human + Agent operating model**. The core principle is that business work should use common execution contracts whether the executor is a Human, a specialized AI Agent, or a collaborative Human + Agent flow.

## What the platform does

### Separate operating workspaces

The platform provides distinct operational contexts:

```text
Platform / Vendor
        ↓
     Reseller
        ↓
      Client
```

These are not merely UI themes. Tenant, role and authorization boundaries prevent downstream workspaces from implicitly controlling upstream operations.

### Unified execution

Business work is represented through shared execution and control concepts:

- WorkItems and execution lifecycle;
- Human and Agent executors;
- delegation/handoff where supported;
- authorization and RBAC;
- policy and approval controls;
- scoped tools and credentials;
- audit/history;
- cancellation/retry and concurrency controls.

Existing Employee entities remain compatibility structures while execution capabilities migrate toward AgentDefinition, AgentInstance and WorkItem abstractions.

### Core product capabilities

The implemented repository includes substantial capability across authentication/JWT, multi-tenancy and tenant isolation, RBAC and scoped API keys, AI execution and usage/audit paths, files/knowledge/memory/conversations, workflows/schedules/approvals, reporting/analytics, billing/commercial boundaries, Platform/Reseller/Client workspaces and unified Human/Agent execution.

Some external integrations are implemented but remain separately classified until real provider/runtime evidence exists.

## Test Center

Phase 12 has productized repeatable verification into a first-class Test Center.

The implemented contract is:

```text
Test Definition
      ↓
Authorized Test Run
      ↓
Tenant/workspace isolation
      ↓
Lifecycle + expiration
      ↓
Persisted result/evidence
      ↓
Run history + artifacts
      ↓
Immutable verification export
      ↓
Authorized customer UI
```

The lifecycle includes queued, running, passed, failed, cancelled and expired states. Persistence safety validation rejects secret-bearing evidence payloads and malformed/non-JSON structures at the model boundary.

Phase 12 is implemented through P12.6. Real runtime operational validation remains a distinct evidence gate from repository CI.

## Where the project is now

- V1.4: frozen architecture foundation.
- V1.5: active Agentic Operating Model extension.
- Phase 11 Unified Execution acceptance: complete.
- Phase 12 Test Center P12.1-P12.6: **implemented / operational hardening**.
- Phase 12 persistence safety hardening: **merged to main**.
- Phase 13 Agent Teams & Marketplace: **design started; implementation gated by Phase 12 operational validation**.
- Phase 14: Scale, Governance & Production, planned.

## Phase 13 design direction

The first Phase 13 slices are contract-first:

1. tenant-scoped TeamDefinition and immutable TeamVersion;
2. authorized tenant installation;
3. WorkItem-backed team execution;
4. evaluation/version evidence;
5. marketplace publication/discovery boundaries;
6. authorized UI surfaces.

Phase 13 must reuse the existing Human + Agent execution substrate and preserve tenant, RBAC, approval, tool, audit, lifecycle, concurrency and evidence boundaries.

## Important evidence boundary

The repository distinguishes:

- implementation evidence;
- automated/CI verification;
- local real-stack validation;
- external production evidence;
- Vendor/Reseller/Client acceptance.

Green CI or a Git release does not by itself prove external production deployment or customer acceptance.
