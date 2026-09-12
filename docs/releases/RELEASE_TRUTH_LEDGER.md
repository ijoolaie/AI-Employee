# Release Truth Ledger

**Last reconciled:** 2026-09-12
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Client acceptance evidence exists.

These states are independent and must not be inferred from release names.

## Current release identities

| Release / candidate | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.4.1` | `f7f5062feb125c7ca50263f74a0e40bc4abfa591` | VERIFIED | **CERTIFIED** — Run `34696339261` | **NOT VERIFIED / no evidence** | Pending |
| `v1.4.0-rc.4` | `4cadd2df003d72de43546466a47e2c66062002c6` | Historical candidate | **CERTIFIED** — Run `34693535048` | No evidence | Pending |
| `v1.3.8` | `fd1e74b6b4c1701f7443efc202bad161ff19618c` | VERIFIED | **CERTIFIED** — Run `34052885700` | **NOT DEPLOYED** — Run `34060615390` failed before remote deployment | Pending |
| `v1.4.0-rc.1` | `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` | Historical candidate | **NOT CERTIFIED** — Run `34497132748` had 1 failed Product Gate | Not eligible | Pending |
| current `main` | Later documentation reconciliation commits after `v1.4.1` | Not a release | **NOT CERTIFIED** — fresh certification required if promoted | Not eligible | Pending |

## v1.4.1 certification checkpoint

Production Certification Run `34696339261` passed for exact SHA `f7f5062feb125c7ca50263f74a0e40bc4abfa591`, with certification job `103560364112`. The release workflow subsequently published tag `v1.4.1` and its edition/runtime release assets.

Certification and release evidence attach to that exact SHA. Subsequent documentation commits are not automatically certified.

## v1.4.1 delivery checkpoint

PR #501 delivered the Self-Hosted edition and four edition profiles/packages. The final release contains customer, reseller, self-hosted and vendor packages, runtime, `EDITION-RELEASE-MANIFEST.json` and `SHA256SUMS`.

The release is an engineering/release-certified snapshot. No external production deployment or customer acceptance is inferred from the published assets.

## Agent capability workstream

The next engineering phases are:

1. Tool Calling contract + E2E.
2. Structured Arguments / JSON Schema fail-closed validation.
3. Multi-step bounded execution.
4. Real provider validation, starting with LM Studio.
5. Exact-SHA release gate for promoted code.

These phases are engineering work, not release identities and not external production certification.

## Production infrastructure baseline

Recommended initial external target is 8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD on Ubuntu 24.04 LTS, with TLS ingress, hardened firewall, encrypted off-host backups and centralized observability. See `docs/current/PRODUCTION_SERVER_BASELINE.md`.

No server provisioning is implied by this recommendation.

## External production boundary

The following remain open regardless of `v1.4.1` certification:

- real production target and deployed-identity verification;
- live provider validation;
- measured production SLO/SLI and error budget;
- real backup/restore/DR with RPO/RTO;
- external Vendor → Reseller → Client runtime isolation/RBAC;
- deployed-target DAST;
- independent penetration test/security review;
- production networking and secret-management lifecycle evidence;
- HA/failure recovery and incident-response rehearsal;
- staffed alert ownership/on-call evidence;
- final external certification and customer acceptance (#210/#269).

## Current interpretation

- Latest published and exact-SHA certified release: **v1.4.1 / `f7f5062f...`**.
- Current `main`: **documentation reconciliation after v1.4.1 — not certified as a new release**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.

## Next action

Preserve the exact-SHA boundary. For external production, deploy only a frozen certified release identity and attach deployment, DR, SLO, security and acceptance evidence to that same SHA. For Agent capability code promoted into a future release, freeze the final SHA and run fresh certification before release publication.
