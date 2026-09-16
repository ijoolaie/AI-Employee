# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-09-16

Three axes remain independent:

- **Release:** `v1.4.1` at exact SHA `f7f5062feb125c7ca50263f74a0e40bc4abfa591`, certified by Production Certification Run `34696339261`.
- **Architecture:** `V1.5 Agentic Operating Model`.
- **Engineering:** Stage 7 external production execution and Stage 8 governed Agent workforce engineering/evidence.

`v1.4.1` is the latest published exact-SHA certified release. Current `main` has subsequent engineering commits and is not automatically certified as a new release.

## Current position

Phase 11 Unified Execution is complete. Phase 12 Test Center is operationally hardened. Phase 13 Agent Teams & Marketplace is engineering complete. Phase 14.1–14.16 tracked engineering is complete/reconciled. PR #501 delivered the Self-Hosted edition and v1.4.1 release assets.

Current `main` also contains the latest Stage 8 governance hardening: PR #514 (policy decision audit bridge), PR #516 (governed AgentInstance replacement workflow) and PR #517 (principal identity propagation through workflow child runs).

Local backend validation on 2026-09-16: **775 passed**; focused Agent/Workflow selection: **229 passed, 546 deselected**.

## Stage 7 — External Production Certification & Customer Acceptance

**Issues:** #210 / #269 / #19 — **ACTIVE / EXTERNAL-PENDING**

| Priority | Work package | Status |
|---|---|---|
| P0 | Immutable release identity | `v1.4.1` published and exact-SHA certified |
| P0 | External production deployment | Pending real infrastructure |
| P0 | Backup/restore & DR | Pending target evidence and measured RPO/RTO |
| P0 | Production SLO/SLI | Engineering contract exists; target measurement pending |
| P0 | Live provider validation | Pending |
| P0 | Vendor → Reseller → Client isolation/RBAC | External evidence pending |
| P0 | DAST / independent security review | External evidence pending |
| P0 | Networking / TLS / secret lifecycle | Target evidence pending |
| P0 | HA/failure recovery | Target rehearsal pending |
| P0 | Incident response / on-call | Live drill pending |
| P0 | Final external certification / customer acceptance | Pending #210/#269 |

### Recommended production infrastructure

Canonical baseline: `docs/current/PRODUCTION_SERVER_BASELINE.md`.

- **Staging:** 4 vCPU / 8 GB RAM / 100 GB SSD.
- **Initial production:** 8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD.
- **Growth:** 12–16 vCPU / 32 GB RAM / 250 GB+ NVMe/SSD.
- Ubuntu 24.04 LTS, fixed/public IP, TLS ingress, hardened firewall, encrypted off-host backups and centralized observability.
- Kubernetes is not required for the first external target; a hardened Docker-based deployment is sufficient when recovery and security controls are verified.
- GPU is optional for remote-provider inference and mainly relevant to local model inference/GPU OCR.

## Stage 8 — AI Company Operating Model Foundation

**Class:** PRODUCT / ARCHITECTURE — **ENGINEERING FOUNDATION IMPLEMENTED / ACCEPTANCE-EVIDENCE ACTIVE / NOT A RELEASE**

The governed workforce foundation is now substantially implemented on mainline. Recent hardening has closed several gaps that were still listed as open in earlier audit documents.

### Confirmed implementation advances

- **PR #514:** policy decisions are connected to the audit bridge with execution-trace metadata.
- **PR #516:** AgentInstance replacement is a distinct governed workflow with lineage, permission, cutover preparation and predecessor retirement controls.
- **PR #517:** workflow child runs preserve the parent AgentInstance principal identity evidence.
- Repository validation on 2026-09-16: **775 passed**.

### Remaining Stage 8 acceptance/evidence work

Stage 8 is not yet declared fully complete/certified because the blueprint requires implementation, automated validation, operational evidence and documentation traceability together.

1. Complete principal identity evidence across every protected agent action.
2. Complete tool allow-list, side-effect and high-risk approval-binding evidence.
3. Complete agent-to-agent trust end-to-end acceptance and audit evidence.
4. Complete risk-tier and evaluation/publication gate evidence.
5. Complete usage attribution, hard budget-stop and runaway-execution evidence where gaps remain.
6. Reconcile all exit criteria to exact implementation/test commit SHAs.
7. Run fresh exact-SHA certification before promoting Agent capability code into a release.

### Agent capability execution phases

#### Agent-1 — Tool Calling Contract

- expose allow-listed tool definitions to providers;
- parse structured provider tool calls;
- enforce registry/tool authorization;
- execute tool and return a structured result to the model;
- prove the complete model → tool → result → final-answer cycle with a fake provider.

**Exit:** deterministic E2E acceptance test passes without unauthorized tool execution.

#### Agent-2 — Structured Arguments

- canonical JSON Schema per tool;
- provider-neutral argument validation;
- reject unknown tool, empty/duplicate call IDs, non-object arguments and malformed calls;
- reject missing required fields, extra fields and wrong types before side effects;
- preserve auditable validation failure.

**Exit:** valid arguments execute; every invalid class fails closed before handler side effect.

#### Agent-3 — Multi-step Execution

- support repeated model → tool → result cycles;
- prove Tool A → Tool B → final answer;
- enforce `AI_MAX_TOOL_ITERATIONS` / autonomous step limits;
- prevent runaway loops and duplicate execution;
- preserve correlation, usage/cost and audit context.

**Exit:** ordered multi-step E2E passes and hard bounds stop excessive loops.

#### Agent-4 — Provider Validation

- LM Studio is the first real-provider validation target because it can run locally without external API spend;
- validate Anthropic integration when intentionally configured;
- keep provider behavior behind the existing provider interface;
- never bypass registry/schema/execution-fence controls for provider-specific behavior.

**Exit:** real provider produces compatible calls through the same safety boundary.

#### Agent-5 — Release Gate

Any code change in the Agent capability workstream that is promoted into a release must receive CI and fresh exact-SHA Production Certification. Test-only documentation changes do not inherit or alter certification; code changes require a new certified SHA before release promotion.

## Stage 9 — Autonomous Workforce Optimization

Stage 9 should build optimization above the now-governed execution substrate, not repeat Stage 8 foundation work.

Future controlled capabilities include:

- capability-aware workload routing;
- model selection by task, risk and cost;
- agent evaluation and measurable fitness signals;
- version fitness, promotion and rollback;
- predictive workforce capacity planning;
- governed autonomous scaling and workload rebalancing;
- optimization feedback loops with human governance above the optimizer.

**Stage 9 entry rule:** derive implementation scope from the final Stage 8 exit audit and actual optimizer gaps. Do not treat already-implemented lifecycle, identity, replacement, tool-policy or bounded-execution primitives as missing work.

## Stage 10 — AI Company Operating System

Long-term product vision: organization-wide command, policy-governed autonomy, agent/version registry, workforce analytics, orchestration and tenant-safe operations. This is not a current implementation claim.

## Cross-cutting Definition of Done

Every stage must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditable identity, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation.

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, production-like validation, synthetic load and simulated providers are engineering/release evidence only. They do not substitute for live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.

## Canonical companion records

- `docs/00_START_HERE/VERSIONING_TRUTH.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/00_START_HERE/CURRENT_PRIORITIES.md`
- `docs/current/PRODUCTION_SERVER_BASELINE.md`
- `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/current/STAGE_8_IMPLEMENTATION_STATUS.md`
- `docs/engineering/STAGE_8_GOVERNANCE_AUDIT_CHECKLIST.md`
- `docs/blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md`
- `docs/releases/RELEASE_TRUTH_LEDGER.md`
