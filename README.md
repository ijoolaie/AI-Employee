# AI Employee Platform

**Latest published/certified release:** `v1.4.16` — exact certified SHA `434a0c4a4501af08a393faaf58092add764df2a2`

**Exact-SHA Production Certification:** Run `37188879277` — PASS; Job `111396657270` — PASS

**Current `main`:** post-release engineering head; **NOT release-certified**. Resolve the mutable branch head directly from Git metadata.

**Production deployment:** **NOT CLAIMED / NOT VERIFIED**

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving toward a **Human + Agent operating model** with shared authorization, tools, approvals, audit and lifecycle controls.


## Versioning truth

- **Release:** immutable product snapshot. Latest published: `v1.4.16`.
- **Architecture:** current baseline: `V1.5`.
- **Engineering program:** external production execution and governed Agent workforce engineering.

See `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## v1.4.16 release truth

- Tag: `v1.4.16`
- SHA: `434a0c4a4501af08a393faaf58092add764df2a2`
- Certification run: `37188879277` — PASS
- Certification job: `111396657270` — PASS
- Evidence artifact: `production-certification-evidence-v1.4.16-434a0c4a4501af08a393faaf58092add764df2a2`
- Evidence artifact SHA-256: `7af4640395aefcffe0485fc3b276dad0dc794a97333efe59d531ef8af74d3d70`
- Production deployment: **NOT CLAIMED / NOT VERIFIED**
- W10 Internal Company Dogfood on the same SHA: **PASS** — Run `37189332690` / Job `111398049109`

Historical release records remain immutable; see `docs/releases/RELEASE_TRUTH_LEDGER.md`.


## W11 Humanized Employee Identity & Visual Presentation

The post-v1.4.11 workforce program now gives each Employee a stable display identity with an optional avatar reference. The initial foundation is intentionally lightweight: no GPU inference, image generation, camera processing, lip-sync or video streaming is introduced. Real-time visual chat remains a future provider-backed capability and requires its own governance and evidence boundary.

See `docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md` for the W11 contract and evidence boundary.

## Current Agent capability workstream

The existing architecture already contains the core mechanics for:

1. **Tool Calling** — tool schemas, allow-listed registry, tool execution and result handoff.
2. **Structured Arguments** — JSON-schema-defined tool arguments and registry validation.
3. **Multi-step** — bounded model → tool → result → model execution cycles.

The next engineering work is explicit acceptance and hardening, not rebuilding these capabilities from zero:

```text
Agent-1  Tool Calling Contract + E2E
   ↓
Agent-2  Structured Arguments / Fail-Closed Validation
   ↓
Agent-3  Multi-step / Bounded Execution
   ↓
Agent-4  Real Provider Validation (LM Studio first)
   ↓
Agent-5  Exact-SHA Release Gate
```

This workstream is separate from external production execution/certification.

## Production server baseline

Recommended initial production target:

- **8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD**
- Ubuntu 24.04 LTS
- fixed/public IP with hardened firewall and TLS ingress
- encrypted off-host backups
- centralized logs, metrics and alerting

Staging: 4 vCPU / 8 GB / 100 GB. Growth: 12–16 vCPU / 32 GB / 250 GB+.

GPU is not required when using a remote model provider; it becomes relevant for intentional local model inference or GPU OCR.

See `docs/current/PRODUCTION_SERVER_BASELINE.md`.

## External production boundary

Still pending target-specific evidence for real deployment, backup/restore and measured RPO/RTO, production SLO/SLI, live providers, Vendor → Reseller → Client isolation/RBAC, DAST/security review, networking/secrets, HA/recovery, incident response/on-call and final external certification/customer acceptance (#210/#269).

CI, production-like infrastructure and simulated providers are engineering/release evidence only.

## Start Here

1. `docs/00_START_HERE/VERSIONING_TRUTH.md`
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. `docs/00_START_HERE/CURRENT_STATUS.md`
4. `docs/00_START_HERE/CURRENT_PRIORITIES.md`
5. `docs/DOCUMENTATION_INDEX.md`
6. `docs/current/PRODUCTIZATION_ROADMAP.md`
7. `docs/current/PRODUCTION_SERVER_BASELINE.md`
8. `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
9. `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
10. `docs/current/EXTERNAL_PRODUCTION_EXECUTION_PACK_2026-09-26.md`

## Release rules

- Keep `main` as vendor source of truth.
- Never mutate a published release for one reseller/client.
- Keep secrets and tenant data outside source/artifacts.
- Preserve tenant isolation and RBAC for humans and agents.
- Every privileged action is auditable.
- Certification never transfers automatically across SHAs.
- Production claims require target-specific evidence.

The repository includes an Apache-2.0 `LICENSE` file.

## Virtual AI Company Headquarters

The roadmap is expanding beyond a traditional AI dashboard toward a visual AI Company Headquarters. The Presentation Layer can show the CEO office, employee departments, project rooms, meetings, real employee work states and company growth while the governed Workforce Runtime remains the single source of truth.

The experience is game-like in presentation but enterprise-grade in semantics. Office visuals, avatars, clothing, themes and cosmetics never grant permissions or bypass governance.

Planned monetization includes recurring AI Employee/project/usage/skill subscriptions, marketplace commissions for third-party employees/skills/workflows, and premium office/avatar/clothing/theme/white-label experiences.

Planned product phases are W11–W21. They are not release-certified functionality until exact-SHA implementation and evidence exist.

See docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md for the authoritative roadmap and architecture boundaries.

### Current Virtual Office implementation

The first W12 Virtual Office foundation is now implemented on post-v1.4.11 mainline: a tenant-scoped read-only office-state API and customer office UI derive employee presentation state from existing governed Employee/Run/WorkflowApproval data. This is not release-certified yet; exact-SHA CI/certification remains **NOT RUN / NOT VERIFIED**.
