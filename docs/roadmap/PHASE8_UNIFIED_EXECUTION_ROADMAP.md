# Phase 8 — Unified Execution Roadmap

**Status:** ACTIVE
**Baseline:** 2026-08-28

## 8.1 Contract foundation — COMPLETE
- WorkItem domain contract
- AgentDefinition / AgentInstance contracts
- Executor abstraction
- HumanExecutor compatibility model
- lifecycle/state machine
- security and audit contract
- API contract

## 8.2 Persistence — COMPLETE
- [x] WorkItem persistence model
- [x] AgentDefinition persistence model
- [x] AgentInstance persistence model
- [x] Alembic migration
- [x] tenant-scoped indexes / idempotency constraint
- [x] model registration
- [x] unit contract tests
- [x] execute migration against CI database
- [x] compatibility mapping to Employee/Run
- [x] database isolation integration tests

## 8.3 Execution service — SUBSTANTIALLY COMPLETE
- [x] unified executor dispatch
- [x] Human execution path
- [x] Agent execution path
- [ ] cancellation/retry/timeout
- [x] result/error normalization

## 8.4 Delegation and handoff — COMPLETE
- [x] Human → Agent
- [x] Agent → Human
- [x] Agent → Agent
- [x] approval-gated delegation boundary
- [x] context and artifact transfer

## 8.5 Policy and tools — COMPLETE
- [x] capability authorization boundary
- [x] tool scopes boundary
- [x] budget boundary
- [x] approval policies
- [x] secrets boundaries
- [x] per-agent concurrency

## 8.6 Observability and economics — COMPLETE
- [x] structured audit/execution events
- [x] usage/cost attribution fields
- [x] execution correlation/traces
- [x] duration/latency metrics

## 8.7 Test Center — COMPLETE
- [x] tenant-scoped test runs
- [x] safe-mode mutation guard
- [x] run evidence lifecycle/export

## 8.8 Workspace UX — IN PROGRESS
- [x] tenant-safe execution workspace projection
- [x] lifecycle/executor/approval visibility
- [x] correlated telemetry visibility
- [x] secret-safe UI projection
- [ ] frontend workspace integration
- [ ] operator filtering/actions

## 8.9 Agent teams — NEXT
- [ ] team execution contract
- [ ] role/member routing
- [ ] shared context and artifact exchange
- [ ] team-level approval/policy boundary
- [ ] team telemetry aggregation

## Exit gate

Phase 8 cannot be declared complete until a representative business operation can be executed by a Human and by an Agent through the same WorkItem contract, with identical tenant isolation, authorization, approval, audit and usage semantics.
