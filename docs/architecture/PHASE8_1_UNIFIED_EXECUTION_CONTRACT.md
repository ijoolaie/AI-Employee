# Phase 8.1 — Unified Human + Agent Execution Contract

**Status:** CANONICAL DESIGN BASELINE
**Date:** 2026-08-27

## Goal

Create one execution contract so a WorkItem can be performed by a Human, a specialized Agent, or a sequence of both without creating separate business semantics.

## Core entities

### WorkItem

The canonical business unit of executable work.

Required concepts:

- tenant ownership
- title/description and structured input
- lifecycle state
- priority
- requester/owner
- executor reference
- parent/related WorkItems
- timestamps and idempotency key
- policy context
- approval state
- result/error summary

### AgentDefinition

Reusable specification of a specialized Agent.

Includes:

- capabilities
- allowed tools
- model/provider policy
- system instructions
- input/output contract
- safety/policy requirements
- version
- lifecycle state

### AgentInstance

Tenant-scoped runtime/deployment of an AgentDefinition.

Includes:

- tenant scope
- definition/version
- configuration references
- availability/lifecycle
- cost budget
- concurrency limits
- audit metadata

### Executor

A common execution interface implemented by:

- HumanExecutor
- AgentExecutor

The business layer must not branch on executor type for core WorkItem semantics.

## Lifecycle

```text
DRAFT → READY → ASSIGNED → RUNNING →
  SUCCEEDED
  FAILED
  BLOCKED
  CANCELLED
  WAITING_APPROVAL
```

Handoff and delegation create explicit execution events and preserve the WorkItem identity and audit trail.

## Security boundary

Authorization is evaluated against the WorkItem, tenant, executor identity, requested capability and tool scope. An Agent must never receive broader authority than the Human or policy context that authorized its work.

## Compatibility

Existing Employee/EmployeeVersion/Run models remain supported during migration. A compatibility adapter maps legacy execution into WorkItem/Executor concepts. Destructive renames are explicitly out of scope for Phase 8.1.

## Observability

Every execution attempt must support correlation with:

- WorkItem ID
- executor ID/type
- tenant ID
- approval decision
- tools used
- token/usage/cost data where applicable
- audit event IDs
- parent/handoff relationship

## Acceptance gates

Phase 8.1 is complete when domain contracts are stable, legacy compatibility is explicit, authorization semantics are defined, lifecycle transitions are testable, and the API/UI contract can be implemented without executor-specific business duplication.
