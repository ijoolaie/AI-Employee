# AI Employee Platform

**Current implementation baseline:** `V1.4 ACTIVE EXECUTION BASELINE`

**Next architecture extension:** `V1.5 AGENTIC OPERATING MODEL`

**Latest certified vendor release:** `v1.2.0`

This repository is the vendor source of truth for the AI Employee Platform. The platform is **Agent-first, not Employee-first**: every supported business capability in Platform, Reseller and Client is designed to be executable by a Human, a specialized Agent, or both through the same WorkItem, authorization, tool, approval and audit contracts.

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

## Documentation

Read in this order:

1. `docs/blueprint/V1.4_MASTER_BLUEPRINT.md` — frozen V1.4 foundation.
2. `docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md` — Human + Agent operating model.
3. `docs/current/PRODUCTIZATION_ROADMAP.md` — authoritative phase roadmap.
4. `docs/current/10_RELEASE_CHANNELS_AND_EDITION_MODEL.md`
5. `docs/current/11_DELIVERY_PACKAGE_SPEC.md`
6. `docs/current/40_GITHUB_MAIN_VERIFICATION_2026-08-26.md`

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

## Release rules

- Keep `main` as vendor source of truth.
- Never mutate a published release for one reseller/client.
- Keep secrets and tenant data outside source/artifacts.
- Preserve tenant isolation and RBAC for both humans and agents.
- Every privileged action is auditable.
- CI/repository evidence is not production evidence.
- Maintain one authoritative Alembic graph.

## Current release truth

- Current implementation baseline: `V1.4`
- Next architecture extension: `V1.5 Agentic Operating Model`
- Latest certified vendor release: `v1.2.0`
- V1.4 remains a frozen architecture baseline, not a certified `v1.4.0` product release.

## Migration note

Do not destructively rename the existing Employee model. New execution capabilities should use the V1.5 Agent/WorkItem abstractions and compatibility adapters. Run `alembic upgrade head` and `alembic check`; never stamp a database merely to hide a migration mismatch.

## License

No explicit open-source license is declared yet. Public visibility alone does not grant reuse rights.
