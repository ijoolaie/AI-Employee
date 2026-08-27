# Phase 8 — Unified Execution Roadmap

**Status:** ACTIVE
**Baseline:** 2026-08-27

## 8.1 Contract foundation — COMPLETE

- WorkItem domain contract
- AgentDefinition / AgentInstance contracts
- Executor abstraction
- HumanExecutor compatibility model
- lifecycle/state machine
- security and audit contract
- API contract

## 8.2 Persistence — IN IMPLEMENTATION

- [x] WorkItem persistence model
- [x] AgentDefinition persistence model
- [x] AgentInstance persistence model
- [x] Alembic migration
- [x] tenant-scoped indexes / idempotency constraint
- [x] model registration
- [x] unit contract tests
- [ ] execute migration against CI database
- [ ] compatibility mapping to Employee/Run
- [ ] database isolation integration tests

## 8.3 Execution service

- unified executor dispatch
- Human execution path
- Agent execution path
- cancellation/retry/timeout
- result/error normalization

## 8.4 Delegation and handoff

- Human → Agent
- Agent → Human
- Agent → Agent
- approval-gated delegation
- context and artifact transfer

## 8.5 Policy and tools

- capability authorization
- tool scopes
- approval policies
- secrets boundaries
- per-agent budgets/concurrency

## 8.6 Observability and economics

- audit events
- usage/cost attribution
- execution traces
- SLA/latency metrics

## 8.7 Test Center

Every Platform, Reseller and Client workspace gets role-aware test operations. Tests must support Human execution and Agent execution through the same WorkItem contract.

## 8.8 Workspace UX

Build role-specific surfaces only after the shared execution API is stable:

- Platform control plane
- Reseller portfolio/service operations
- Client business workspace

## 8.9 Agent teams

Specialist coordination, routing, escalation and team-level policies.

## Exit gate

Phase 8 cannot be declared complete until a representative business operation can be executed by a Human and by an Agent through the same WorkItem contract, with identical tenant isolation, authorization, approval, audit and usage semantics.
