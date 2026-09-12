# Current Status

**Last reconciled:** 2026-09-12
**Latest published release:** `v1.4.1`
**Release commit:** `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
**Exact-SHA Production Certification:** Run `34696339261` — SUCCESS
**Current engineering mainline:** `main` after v1.4.1 release/documentation reconciliation
**Current status:** ENGINEERING-CERTIFIED RELEASE / EXTERNAL PRODUCTION GATES PENDING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

`v1.4.1` is the current published release and its exact SHA passed the repository's Production Certification suite. Certification is bound to that SHA only. There is still no verified external production deployment of `v1.4.1` recorded in repository evidence.

## v1.4.1 release checkpoint

- PR #501 — Self-Hosted edition and release asset publication — merged.
- Release tag: `v1.4.1`.
- Release target SHA: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`.
- Certification run: `34696339261` — SUCCESS.
- Certification job: `103560364112` — SUCCESS.
- Four edition packages plus runtime, manifest and SHA256SUMS were published.
- External deployment, live-provider acceptance and customer acceptance remain pending.

Historical `v1.3.8` remains frozen at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

## Latest hardening sequence

Key merged execution-boundary hardening includes PRs #464, #465, #466, #467, #468, #470, #473, #475, #477, #479, #482, #486, #487 and #499. These establish crash-safe handoff, approval/outbox safety, workflow replay fencing, durable execution leases, concurrent execution admission fencing and workflow FK integrity without weakening repository controls.

## Current Agent capability workstream

The next focused engineering work is **Tool Calling + Structured Arguments + Multi-step execution**. These are substantially implemented in the current architecture; the objective is to turn the existing capability into explicit acceptance contracts and provider-neutral guardrails.

### Capability phases

| Phase | Capability | Scope | Exit gate |
|---|---|---|---|
| Agent-1 | Tool Calling | Tool schema exposure, allow-listing, provider tool-call parsing, execution and result handoff | Fake-provider E2E proves model → tool → result → final answer |
| Agent-2 | Structured Arguments | JSON Schema contracts, valid/invalid argument handling, unknown-tool and malformed-call rejection before side effects | Missing/extra/wrong-type/unknown arguments fail closed |
| Agent-3 | Multi-step | Multiple sequential tool calls, bounded iterations/steps, loop safety and auditability | Tool A → Tool B → final answer passes with hard bound |
| Agent-4 | Provider Validation | LM Studio first; cloud provider validation where credentials are intentionally available | Real provider produces compatible structured calls without bypassing guards |
| Agent-5 | Release Gate | Re-run full CI/certification for any code promoted into a release | Exact final SHA has fresh evidence |

This workstream is **not** external production certification and does not replace Stage 7.

## Production infrastructure baseline

Recommended starting production host:

- 8 vCPU
- 16 GB RAM
- 150–200 GB NVMe/SSD
- Ubuntu 24.04 LTS
- fixed/public IP with hardened firewall and TLS ingress
- automated daily encrypted backups outside the host/failure domain
- centralized logs/metrics and alerting

For testing/staging, 4 vCPU / 8 GB / 100 GB is sufficient. For serious growth, 12–16 vCPU / 32 GB / 250 GB+ is the recommended next tier. GPU is optional and mainly relevant to local model inference or GPU-dependent OCR.

Canonical server baseline: `docs/current/PRODUCTION_SERVER_BASELINE.md`.

## External production gates

Still pending target-specific evidence:

- real production infrastructure and immutable deployed identity;
- live provider validation;
- real backup/restore and measured RPO/RTO;
- production SLO/SLI and error budget;
- external Vendor → Reseller → Client runtime isolation/RBAC;
- authenticated DAST where applicable;
- independent penetration testing/security review;
- production networking/TLS/egress controls;
- secret-manager lifecycle and rotation/recovery;
- HA/failure recovery rehearsal;
- incident-response and on-call drill;
- final external certification and customer acceptance (#210/#269).

## Evidence boundary

CI, repository tests, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.

## Security rule

Never commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
