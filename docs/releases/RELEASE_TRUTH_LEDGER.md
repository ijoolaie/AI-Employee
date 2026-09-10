# Release Truth Ledger

**Last reconciled:** 2026-09-10  
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
| `v1.3.8` | `fd1e74b6b4c1701f7443efc202bad161ff19618c` | VERIFIED | **CERTIFIED** — Run `34052885700` | **NOT DEPLOYED** — Run `34060615390` failed before remote deployment | Pending |
| `v1.4.0-rc.1` | `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` | Candidate under validation | **NOT CERTIFIED** — Run `34497132748` has 1 failed Product Gate | Not eligible for deployment certification | Pending |

## v1.4.0-rc.1 certification reconciliation

The current engineering mainline is `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`, submitted to Production Certification as `v1.4.0-rc.1`.

Production Certification Run `34497132748`, job `102938351658`, completed with one failed Product Gate:

**`Unified WorkItem Agent real-stack`**

The gate reaches the commercial-license fixture pass and then reports `UNIFIED AGENT WORKITEM REAL-STACK CERTIFICATION FAIL:` with an empty assertion message.

The Human WorkItem real-stack gate and the other Product Gates pass. The remaining Agent gate is therefore the current release blocker.

The required investigation path is:

```text
Agent WorkItem
  → assignment
  → AgentExecutionAdapter
  → Run creation
  → queue dispatch
  → Run execution
  → governance/license checks
  → terminal state
  → certification assertion
```

A generic retry is not sufficient evidence of resolution. After correction, the complete required engineering gates must pass on the exact corrected HEAD and Production Certification must be rerun against that exact SHA.

## v1.3.8 reconciliation

The `v1.3.8` Git tag resolves directly to commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

Production certification Run `34052885700` completed successfully. The run passed the release certification suite.

A controlled deployment was attempted in Run `34060615390`, but the workflow failed before remote deployment because required protected production configuration was unavailable. The actual deployment step and deployed-identity verification were skipped. There is therefore no production deployment evidence from that run.

## Current interpretation

- Latest certified release: **v1.3.8 / `fd1e74b6...`**.
- Current release candidate: **v1.4.0-rc.1 / `b2e2517...`**.
- Current RC certification: **BLOCKED — one Product Gate failed**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.
- Real target DR/SLO/security/perimeter evidence: **PENDING**.

## Next action

Resolve the `Unified WorkItem Agent real-stack` blocker, rerun the required exact-SHA gates, and then rerun Production Certification against the resulting exact SHA. Only a zero-failure certification run may advance the candidate toward deployment.
