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

## 8.3 Execution service — ACTIVE
- [x] unified executor dispatch
- [x] Human execution path
- [x] Agent execution path
- [ ] cancellation/retry/timeout
- [ ] result/error normalization

## 8.4 Delegation and handoff — SUBSTANTIALLY COMPLETE
- [x] Human → Agent
- [x] Agent → Human
- [x] Agent → Agent
- [x] approval-gated delegation boundary
- [x] context and artifact transfer

## 8.5 Policy and tools — IN PROGRESS
- [x] capability authorization boundary
- [x] tool scopes boundary
- [x] budget boundary
- [ ] approval policies
- [ ] secrets boundaries
- [ ] per-agent concurrency

## 8.6 Observability and economics
- [ ] audit events
- [ ] usage/cost attribution
- [ ] execution traces
- [ ] SLA/latency metrics

## 8.7 Test Center

## 8.8 Workspace UX

## 8.9 Agent teams

## Exit gate

Phase 8 cannot be declared complete until a representative business operation can be executed by a Human and by an Agent through the same WorkItem contract, with identical tenant isolation, authorization, approval, audit and usage semantics.
