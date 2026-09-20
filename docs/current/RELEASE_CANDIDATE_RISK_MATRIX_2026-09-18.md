# v1.4.5 Release Candidate Risk Matrix and Evidence Plan

> **Historical v1.4.5 Release Candidate Risk Matrix and Evidence Plan — reconciled 2026-09-20.** This document is retained for historical traceability and is **not the current release/readiness source of truth**.
>
> Current release: **v1.4.7** / exact certified SHA `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`.
> Current source of truth: `docs/releases/RELEASE_TRUTH_LEDGER.md`.


## Release identity

- Engineering candidate baseline: `a9d5cdd`
- Reconciled RC1 commit: `0976537441ebc2560624022bfaabb33096f5011c`
- RC branch: `release/v1.4.5-rc1`
- Published certified release: v1.4.2
- Published certified SHA: `dba0bb672deb1236b6724bb8851526e656f47967`
- v1.4.2 certification does not transfer to RC1.
- RC1 GitHub Actions engineering validation: **10/10 current release-critical workflows PASS**.
- Local production-like certification remains engineering evidence only.

## Release-critical matrix

| Axis | Change | Existing engineering evidence | External validation |
|---|---|---|---|
| AI Gateway | Durable provider-call fence; unknown/ambiguous outcome; replay blocking | `test_ai_gateway_audit_lock.py`; Phase A-E runtime evidence; RC1 CI | Live provider execution and failure/timeout drill |
| Run Recovery | Stale-run sweep; fail-closed recovery; no blind provider replay | `test_run_recovery.py`, `test_run_recovery_worker.py`, HA evidence; RC1 CI | Worker-loss/provider-ambiguity drill on target |
| Agent Governance | Tenant-scoped identity, kill switch, access review, delegation and tool-policy checks | Policy audit bridge tests; Phase C/E evidence; RC1 security gates | Deployed actor matrix and security review |
| Tenant Lifecycle | Suspend/deprovision transitions; child ordering; audit retention | Tenant/RBAC E2E; immutable audit retention evidence; RC1 isolation gate | Deployed Vendor/Reseller/Customer isolation acceptance |
| Celery/Workers | Explicit queues; stale sweep independent of execution redelivery | Worker/recovery tests; HA smoke; RC1 CI | Production load and worker-loss drill |
| HA/Deployment | Deterministic bootstrap; restart recovery; portable Docker handling | Phase 14.10 local certification; RC1 infrastructure/HA gates | Target HA/recovery rehearsal |
| Certification | Exact SHA checkout/assertion and immutable evidence manifest | Workflow inspection; local certification; RC1 workflow validation | Exact final-SHA certification run |

## RC1 engineering gate result

For exact RC1 SHA `0976537441ebc2560624022bfaabb33096f5011c`, the current release-critical GitHub Actions validation completed:

1. Backend CI/regression — **PASS**.
2. AI Gateway durable-call fence regression — **PASS**.
3. Run Recovery and recovery-worker tests — **PASS**.
4. Tenant/RBAC real-stack isolation gate — **PASS**.
5. HA failure/recovery validation — **PASS**.
6. Production compose/infrastructure validation — **PASS**.
7. Ephemeral DAST validation — **PASS**.
8. Repository/security/architecture/observability/rollback gates — **PASS**.

Aggregate engineering workflow result: **10/10 PASS**.

## Combined release-critical gate

RC1 is engineering-validated for the exact SHA above. This is an engineering/release-candidate result only. It does not claim production deployment, external certification, live-provider acceptance, RPO/RTO achievement, or commercial acceptance.
