# v1.4.5 Release Candidate Risk Matrix and Evidence Plan

## Release identity

- Engineering candidate baseline: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- Reconciled release commit: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- RC branch: `main`
- Published certified release: v1.4.2
- Published certified SHA: `dba0bb672deb1236b6724bb8851526e656f47967`
- prior v1.4.2 certification does not transfer to release.
- release GitHub Actions engineering validation: **10/10 release-critical workflows PASS**.
- Local production-like certification remains engineering evidence only.

## Release-critical matrix

| Axis | Change | Existing engineering evidence | External validation |
|---|---|---|---|
| AI Gateway | Durable provider-call fence; unknown/ambiguous outcome; replay blocking | `test_ai_gateway_audit_lock.py`; Phase A-E runtime evidence; release CI | Live provider execution and failure/timeout drill |
| Run Recovery | Stale-run sweep; fail-closed recovery; no blind provider replay | `test_run_recovery.py`, `test_run_recovery_worker.py`, HA evidence; release CI | Worker-loss/provider-ambiguity drill on target |
| Agent Governance | Tenant-scoped identity, kill switch, access review, delegation and tool-policy checks | Policy audit bridge tests; Phase C/E evidence; release security gates | Deployed actor matrix and security review |
| Tenant Lifecycle | Suspend/deprovision transitions; child ordering; audit retention | Tenant/RBAC E2E; immutable audit retention evidence; release isolation gate | Deployed Vendor/Reseller/Customer isolation acceptance |
| Celery/Workers | Explicit queues; stale sweep independent of execution redelivery | Worker/recovery tests; HA smoke; release CI | Production load and worker-loss drill |
| HA/Deployment | Deterministic bootstrap; restart recovery; portable Docker handling | Phase 14.10 local certification; release infrastructure/HA gates | Target HA/recovery rehearsal |
| Certification | Exact SHA checkout/assertion and immutable evidence manifest | Workflow inspection; local certification; release workflow validation | Exact final-SHA certification run |

## release engineering gate result

For exact release SHA `cc94bc9536f4f95680bb7a183313914c116ffcf2`, the current release-critical GitHub Actions validation completed:

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

release is engineering-validated for the exact SHA above. This is an engineering/release-candidate result only. It does not claim production deployment, external certification, live-provider acceptance, RPO/RTO achievement, or commercial acceptance.
