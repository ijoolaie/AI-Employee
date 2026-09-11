# Release Truth Ledger

**Last reconciled:** 2026-09-11  
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
| `v1.4.0-rc.1` | `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` | Historical candidate | **NOT CERTIFIED** — Run `34497132748` had 1 failed Product Gate | Not eligible for deployment certification | Pending |
| current `main` | `649f8ceaedb35c4f9e61a56faaf5c58956821c1d` | Not a release | **NOT CERTIFIED** — no fresh Production Certification yet | Not eligible | Pending |

## Current mainline hardening checkpoint

PR #479 was squash-merged at `649f8ceaedb35c4f9e61a56faaf5c58956821c1d` after all required PR certification gates passed on its exact head `172f0bc1ba9281df4c9aad464d209f8b640505f1`, including Architecture Guard, CI, CodeQL, Runtime Isolation/RBAC, HA Failure Recovery, Production Infrastructure Validation and Ephemeral DAST. Additional Production Observability, Production Rollback & Alerting and Phase 14.14 Security Privacy Compliance workflows also passed on that PR head.

PR #479 closes a race in which a workflow could continue advancing after a timeout/cancellation/terminal-state transition won between child commits. It does not make stale `running` executions retryable.

## Open execution-boundary item

Issue #480 tracks a P1 design for durable lease/fencing and recovery of stale `WorkflowRun` and `Run` records. The recovery model must prevent an old worker from continuing side effects after ownership transfer, preserve provider durable-call fences and child Run identity, and avoid blind replacement execution. This work must remain fail-closed until a durable ownership-transfer protocol is implemented and tested.

## v1.3.8 reconciliation

The `v1.3.8` Git tag resolves directly to commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

Production certification Run `34052885700` completed successfully. The run passed the release certification suite.

A controlled deployment was attempted in Run `34060615390`, but the workflow failed before remote deployment because required protected production configuration was unavailable. The actual deployment step and deployed-identity verification were skipped. There is therefore no production deployment evidence from that run.

## Current interpretation

- Latest certified release: **v1.3.8 / `fd1e74b6...`**.
- Current mainline: **`649f8cea...` — not certified**.
- Previous `v1.4.0-rc.1`: **historical / not certified**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.
- Real target DR/SLO/security/perimeter evidence: **PENDING**.

## Next action

Resolve Issue #480 through a durable lease/fencing and recovery design, add crash/recovery regression coverage, run the complete required exact-SHA gates, and then create a new release candidate and rerun Production Certification against the resulting exact SHA. Only a zero-failure certification run may advance the candidate toward deployment.
