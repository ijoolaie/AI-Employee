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
| `v1.4.0-rc.4` | `4cadd2df003d72de43546466a47e2c66062002c6` | Candidate identity; no external production tag asserted | **CERTIFIED** — Run `34693535048` | **NOT DEPLOYED / no evidence** | Pending |
| `v1.3.8` | `fd1e74b6b4c1701f7443efc202bad161ff19618c` | VERIFIED | **CERTIFIED** — Run `34052885700` | **NOT DEPLOYED** — Run `34060615390` failed before remote deployment | Pending |
| `v1.4.0-rc.1` | `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` | Historical candidate | **NOT CERTIFIED** — Run `34497132748` had 1 failed Product Gate | Not eligible for deployment certification | Pending |
| current `main` | Documentation reconciliation commits after `4cadd2df003d72de43546466a47e2c66062002c6` | Not a release | **NOT CERTIFIED** — fresh certification required for final release promotion | Not eligible | Pending |

## Latest certification checkpoint

Production Certification Run `34693535048` passed for exact SHA `4cadd2df003d72de43546466a47e2c66062002c6` with release identity `v1.4.0-rc.4`. Product Gates reported zero failures and the production-like certification suite completed successfully.

The certification covers the exact candidate SHA only. Documentation reconciliation commits made afterward are intentionally not attributed to that certification. A final release created from the reconciled mainline must receive a fresh exact-SHA certification.

## Post-certification repository hardening/documentation reconciliation

PR #499 was merged before the certified candidate and removed the SQLAlchemy workflow child-identity FK metadata cycle warning using `use_alter=True`, preserving FK targets, `ondelete="SET NULL"`, uniqueness constraints and durable child-run identity semantics.

Following certification, the canonical status, priorities, production-readiness, gap-register and evidence-index documents were reconciled to the current evidence boundary. These documentation-only commits are not a new release and do not inherit the prior certification automatically.

## v1.3.8 reconciliation

The `v1.3.8` Git tag resolves directly to commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

Production certification Run `34052885700` completed successfully. A controlled deployment was attempted in Run `34060615390`, but the workflow failed before remote deployment because required protected production configuration was unavailable. The actual deployment step and deployed-identity verification were skipped. There is therefore no production deployment evidence from that run.

## External production boundary

The following remain open regardless of the `v1.4.0-rc.4` certification:

- real production target and deployed-identity verification;
- live provider validation;
- measured production SLO/SLI and error budget;
- real backup/restore/DR with RPO/RTO;
- external Vendor → Reseller → Client runtime isolation/RBAC;
- deployed-target DAST;
- independent penetration test/security review;
- production networking and secret-management lifecycle evidence;
- HA/failure recovery and incident-response rehearsal on target;
- staffed alert ownership/on-call evidence;
- final external certification and customer acceptance (#210/#269).

## Current interpretation

- Latest exact-SHA certified candidate: **v1.4.0-rc.4 / `4cadd2df...`**.
- Current mainline: **later documentation-reconciled commits — not certified**.
- Historical certified production release: **v1.3.8 / `fd1e74b6...`**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.
- Real target DR/SLO/security/perimeter evidence: **PENDING**.

## Next action

Keep the evidence boundary exact: do not claim external deployment from repository evidence. Before promoting a release, freeze one immutable final SHA, run the complete Production Certification against that exact SHA, then execute the external Stage 7 sequence and attach every external record to that same release identity.
