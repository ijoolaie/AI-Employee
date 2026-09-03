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

The implemented repository includes substantial capability across:

- authentication/JWT;
- multi-tenancy and tenant isolation;
- RBAC and scoped API keys;
- AI execution and usage/audit paths;
- files, knowledge, memory and conversations;
- workflows, schedules and approvals;
- reporting and analytics;
- billing, invoices and commercial boundaries;
- Platform/Reseller/Client workspaces;
- unified Human/Agent execution.

Some external integrations are implemented but remain separately classified until real provider/runtime evidence exists.

## Test Center

Phase 12 is productizing repeatable verification into a first-class Test Center.

The verified backend foundation currently supports:

```text
Test Definition
      ↓
Authorized Test Run
      ↓
Tenant/workspace isolation
      ↓
Lifecycle execution
      ↓
Persisted result
      ↓
Tenant-scoped retrieval
      ↓
Audit/evidence boundary
```

The lifecycle includes queued, running, passed, failed, cancelled and expired states.

The next work extends this foundation with evidence/artifacts, run history, exportable verification records and then authorized UI surfaces.

## Where the project is now

- V1.4: frozen architecture foundation.
- V1.5: active Agentic Operating Model extension.
- Phase 11 Unified Execution acceptance: complete.
- Phase 12 P12.1-P12.3 backend foundation: verified by green CI.
- P12.4-P12.6: next implementation frontier.
- Phase 13: Agent Teams & Marketplace, planned.
- Phase 14: Scale, Governance & Production, planned.

## Important evidence boundary

The repository distinguishes:

- implementation evidence;
- automated/CI verification;
- local real-stack validation;
- external production evidence;
- Vendor/Reseller/Client acceptance.

Green CI or a Git release does not by itself prove external production deployment or customer acceptance.
