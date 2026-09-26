# AI Employee Platform

**Latest published/certified release:** `v1.4.11` — exact certified SHA `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`

**Exact-SHA Production Certification:** Run `35848311037` — PASS; certification is bound to exact `v1.4.11` SHA only.

**Architecture baseline:** `V1.5 Agentic Operating Model` — architecture/operating-model baseline, not a release.

**Current engineering program:** External Production Execution + Governed Agent Workforce Engineering.

**Production deployment:** **PENDING EXTERNAL EXECUTION**

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving toward a **Human + Agent operating model** with shared authorization, tools, approvals, audit and lifecycle controls.

## Versioning truth

- **Release:** immutable product snapshot. Current: `v1.4.11`.
- **Architecture:** current baseline: `V1.5`.
- **Engineering program:** external production execution and governed Agent workforce engineering.

See `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## v1.4.11 release truth

- Tag: `v1.4.11`
- SHA: `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Certification run: `35848311037` — PASS
- Certification job: `107139710452` — PASS
- Evidence artifact: `production-certification-evidence-v1.4.11-rc.1-90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- External production deployment: pending external execution
- Live provider validation/customer acceptance: pending external execution

Historical release records remain immutable; see `docs/releases/RELEASE_TRUTH_LEDGER.md`.

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
