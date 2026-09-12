# AI Employee Platform

**Latest published release:** `v1.4.1` — exact release SHA `f7f5062feb125c7ca50263f74a0e40bc4abfa591`

**Exact-SHA Production Certification:** Run `34696339261` — SUCCESS; certification is bound to the release SHA only.

**Architecture baseline:** `V1.5 Agentic Operating Model` — architecture/operating-model baseline, not a release.

**Current engineering program:** Stage 7 External Production Execution + Stage 8 Governed Agent Workforce Engineering.

**Production deployment:** **NOT VERIFIED / PENDING REAL INFRASTRUCTURE**

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving toward a **Human + Agent operating model** with shared authorization, tools, approvals, audit and lifecycle controls.

## Versioning truth

- **Release:** immutable product snapshot. Current: `v1.4.1`.
- **Architecture:** current baseline: `V1.5`.
- **Engineering stage:** Stage 7 external production execution and Stage 8 governed Agent workforce engineering.

See `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## v1.4.1 release truth

- Tag: `v1.4.1`
- SHA: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
- Certification run: `34696339261` — SUCCESS
- PR #501: Self-Hosted edition and release assets — merged
- External production deployment: not verified
- Live provider validation/customer acceptance: pending

Historical `v1.3.8` remains frozen at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

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

This workstream is separate from Stage 7 external production certification.

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

## Release rules

- Keep `main` as vendor source of truth.
- Never mutate a published release for one reseller/client.
- Keep secrets and tenant data outside source/artifacts.
- Preserve tenant isolation and RBAC for humans and agents.
- Every privileged action is auditable.
- Certification never transfers automatically across SHAs.
- Production claims require target-specific evidence.

The repository includes an Apache-2.0 `LICENSE` file.
