# AI Employee Platform

**Current implementation baseline:** `V1.4 ACTIVE EXECUTION BASELINE`

**Next architecture extension:** `V1.5 AGENTIC OPERATING MODEL`

**Latest published release:** `v1.3.0`

**Current certified controlled-deployment line:** `v1.2.0`

**Explicit production-certified baseline:** `v1.2.1-final`

This repository is the vendor source of truth for the AI Employee Platform. The platform is **Agent-first, not Employee-first**: every supported business capability in Platform, Reseller and Client is designed to be executable by a Human, a specialized Agent, or both through the same WorkItem, authorization, tool, approval and audit contracts.

## Start Here

For the fastest and safest project orientation, read:

1. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
2. `docs/00_START_HERE/CURRENT_STATUS.md`
3. `docs/00_START_HERE/CURRENT_PRIORITIES.md`
4. `docs/DOCUMENTATION_INDEX.md`
5. `docs/current/PRODUCTIZATION_ROADMAP.md`

Do not infer current truth from historical versioned filenames. Git tags, release records and certification evidence are reconciled in `docs/releases/RELEASE_TRUTH_LEDGER.md`.

## Three workspaces

```text
Platform
   |
   +--> Reseller
   |      |
   |      +--> Client
   |
   +--> Internal Platform Operations
```

Each workspace has role-specific UX and tools. No downstream workspace receives implicit control-plane access to the workspace above it.

## Human + Agent execution

```text
WorkItem
   |
   +--> Human
   |
   +--> Agent
   |
   +--> Human + Agent
   |
   +--> Auto
```

Agents are specialized workers, not merely renamed Employees. Existing Employee entities remain compatibility structures while execution migrates to `AgentDefinition`, `AgentInstance` and `WorkItem`.

## Test Center

**Platform, Reseller and Client all expose a first-class Test Center from the main dashboard.** It provides role-aware health, security, Agent, tool, workflow, handoff, approval, RAG, memory, integration, webhook, usage, billing/sandbox, worker, model and E2E tests with safe-mode controls and persisted evidence.

## V1.5 execution sequence

```text
Phase 8  Unified Execution Foundation
   ↓
Phase 9  Platform Command Center
   ↓
Phase 10 Reseller Operations
   ↓
Phase 11 Client Business Workspace
   ↓
Phase 12 Test Center & Evidence
   ↓
Phase 13 Agent Teams / Marketplace
   ↓
Phase 14 Scale / Governance / Production
```

## Current position

- Phase 11 Unified Execution acceptance: **COMPLETE**.
- Phase 12 Test Center P12.1-P12.6: **IMPLEMENTED / OPERATIONAL HARDENING**.
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**.
- Phase 14.1–14.9: **ENGINEERING COMPLETE**.
- Phase 14.10 External Production / Customer Acceptance: **EXTERNAL-PENDING**.

Phase 14 engineering covered queue/worker isolation, concurrency/backpressure, routing/scheduling, cost controls, SLO instrumentation, DR/backup/restore, security/compliance hardening, regression/release gates and incident response. The remaining Phase 14.10 gate requires independent external evidence; CI alone cannot establish production certification or customer acceptance.

## Release rules

- Keep `main` as vendor source of truth.
- Never mutate a published release for one reseller/client.
- Keep secrets and tenant data outside source/artifacts.
- Preserve tenant isolation and RBAC for both humans and agents.
- Every privileged action is auditable.
- CI/repository evidence is not production evidence.
- Maintain one authoritative Alembic graph.
- Reconcile every release tag to its underlying commit.
- Never inherit certification or acceptance evidence across different SHAs.

## Active external gates

- #210 — consolidated immutable release / external-production gate.
- #19 — Vendor → Reseller → Client runtime isolation/RBAC evidence.
- #269 — Phase 14.10 evidence package and acceptance decision boundary.

These gates remain open until independent evidence is reconciled to one exact accepted release identity.

## Migration note

Do not destructively rename the existing Employee model. New execution capabilities should use the V1.5 Agent/WorkItem abstractions and compatibility adapters. Run `alembic upgrade head` and `alembic check`; never stamp a database merely to hide a migration mismatch.

## License

The repository includes an Apache-2.0 `LICENSE` file. See `LICENSE` for the governing terms.
