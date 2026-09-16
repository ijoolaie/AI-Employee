# Stage 8 Implementation Status Report

**Reconciled:** 2026-09-16
**Current engineering mainline at audit time:** `1c8c3ee2fc933148f90e967e18167fe602d0ad00`

## Purpose

This document reconciles the Stage 8 design requirements with current repository implementation, automated validation and evidence boundaries. It deliberately does not convert implementation into production certification.

## Current validation baseline

Status: **Verified locally**

Evidence from the 2026-09-16 repository run:

- `pytest backend/tests -k "agent or workflow"` → **229 passed, 546 deselected**.
- `pytest backend/tests` → **775 passed**.
- The concurrency test that initially failed because PostgreSQL was unavailable passed after PostgreSQL was started.

These are repository engineering results only.

## Recent implementation changes that supersede the older audit record

### PR #514 — policy decision audit bridge

Merged. Policy decisions now feed the audit bridge with execution-trace metadata including WorkItem, run, tool-call, approval-request and delegation context.

### PR #516 — governed AgentInstance replacement

Merged. Replacement is now an explicit workforce-proposal kind with predecessor lineage, dedicated replacement permission, cutover preparation/cutover endpoints, governance-chain checks, predecessor draining and auditable activation/retirement continuity.

### PR #517 — principal identity propagation

Merged as the current mainline commit. `agent_instance_id` is preserved when workflow child runs are created, including parallel-branch and workflow-step child runs, and is included in run audit metadata.

## Exit-criteria audit

| Stage 8 exit criterion | Current classification | Evidence / reason |
|---|---|---|
| AgentDefinition / AgentTemplate / AgentInstance are distinct enforced concepts | **IMPLEMENTED / VALIDATED** | Distinct models/services and lifecycle tests exist. |
| Every active agent has unique identity and human sponsor/owner | **IMPLEMENTED / PARTIAL EVIDENCE** | AgentIdentity is first-class and sponsor/owner fields exist; complete protected-action evidence is still being reconciled. |
| Tenant isolation at data, memory, tools and execution boundaries | **IMPLEMENTED / VALIDATED FOR CURRENT TEST SCOPE** | Existing security/governance tests cover tenant and authorization boundaries; external target evidence remains separate. |
| Per-action authorization | **IMPLEMENTED / VALIDATED FOR CURRENT POLICY SCOPE** | Agent policy engine evaluates lifecycle, identity, access review, delegation, tool and permission conditions and records decisions. |
| Agent-to-agent trust explicit and auditable | **PARTIAL / ACCEPTANCE GAP** | Delegation primitives exist, but dedicated end-to-end trust acceptance remains an explicit evidence gap. |
| Risk tiers determine autonomy and approval requirements | **PARTIAL / EVIDENCE GAP** | Risk tiers and approval-aware policy inputs exist; full end-to-end acceptance evidence is not yet reconciled. |
| High-impact actions cannot bypass approval | **IMPLEMENTED FOR GOVERNED TOOL APPROVAL PATH / EVIDENCE GAP** | Policy path binds approval context to run/tool-call/arguments; full coverage still needs audit evidence. |
| Workforce creation and retirement are governed lifecycle transitions | **IMPLEMENTED / VALIDATED** | Lifecycle state machine and workforce proposal paths are implemented; retirement is terminal. |
| Evaluation gates block unsafe publication | **PARTIAL / EVIDENCE GAP** | Evaluation and publication concepts exist; full publication-gate certification evidence remains to be reconciled. |
| Usage and cost are attributable and budgeted | **PARTIAL / EVIDENCE GAP** | Usage/cost infrastructure exists, but Stage 8 acceptance evidence for budget enforcement is not yet complete. |
| Audit records are complete and searchable | **PARTIAL / EVIDENCE GAP** | Policy audit bridge, lifecycle events and workflow identity propagation exist; completeness across every protected path is not yet proven. |
| Kill-switch / revocation is tested | **IMPLEMENTED / VALIDATED FOR CURRENT GOVERNANCE SCOPE** | Kill-switch, identity revocation and lifecycle denial paths are present in policy enforcement/tests. |
| Customer installation is tenant-safe | **IMPLEMENTED / CURRENT SCOPE** | Tenant-scoped marketplace/team installation controls exist; external customer acceptance remains pending. |
| Tool Calling / Structured Arguments / bounded Multi-step are accepted | **IMPLEMENTED CORE / ACCEPTANCE WORKSTREAM** | Runtime mechanics and schema/iteration controls exist; explicit provider-neutral E2E and real-provider acceptance remain release-gate work. |
| Production evidence exists on the promoted release SHA | **NOT COMPLETE** | `v1.4.1` is certified, but current main contains later engineering commits and is not a newly certified release. |

## Remaining Stage 8 gaps

1. Complete principal identity evidence across every protected agent action, not only workflow child propagation.
2. Complete tool allow-list, side-effect and approval-binding acceptance evidence.
3. Complete agent-to-agent trust end-to-end acceptance and audit evidence.
4. Complete risk-tier/approval acceptance evidence across high-impact actions.
5. Complete evaluation/publication gate evidence.
6. Complete usage attribution, hard budget-stop and runaway-execution evidence where not already covered by existing tests.
7. Map all evidence to exact commit SHAs and run a fresh release-candidate certification before release promotion.

## Stage 7 boundary remains external

No repository test, local Docker run, simulated provider or CI result substitutes for:

- real production deployment;
- measured production SLO/SLI and error budget;
- real backup/restore/DR RPO/RTO;
- live provider acceptance on the deployed target;
- deployed Vendor → Reseller → Client isolation/RBAC;
- deployed-target DAST and independent security review;
- networking/TLS/secret lifecycle evidence;
- HA/failure recovery and incident/on-call rehearsal;
- final customer acceptance.

## Stage 9 readiness note

Stage 9 should build optimization above the governed execution substrate, not duplicate Stage 8 foundations. Candidate frontier areas are capability-aware routing, task/risk/cost-aware model selection, agent fitness and version fitness, predictive workforce capacity planning, governed scaling/rebalancing and optimization feedback loops.

Stage 9 implementation should be derived from the remaining Stage 8 gaps and actual optimizer requirements, with human governance above autonomous optimization.

## Certification rule

A Stage 8 capability is complete only when implementation, automated validation, operational evidence and documentation traceability exist together. Certification never transfers automatically across SHAs.
