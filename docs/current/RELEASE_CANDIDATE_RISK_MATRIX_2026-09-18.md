# v1.4.5 Release Candidate Risk Matrix and Evidence Plan

## Release identity

- Engineering candidate code baseline: `a9d5cdd`
- Current reconciled repository baseline: `fe26630`
- Published certified release: v1.4.2
- Published certified SHA: `dba0bb672deb1236b6724bb8851526e656f47967`
- v1.4.2 certification does not transfer to this candidate.

## Release-critical matrix

| Axis | Change | Existing engineering evidence | External validation |
|---|---|---|---|
| AI Gateway | Durable provider-call fence; unknown/ambiguous outcome; replay blocking | `test_ai_gateway_audit_lock.py`; Phase A-E runtime evidence | Live provider execution and failure/timeout drill |
| Run Recovery | Stale-run sweep; fail-closed recovery; no blind provider replay | `test_run_recovery.py`, `test_run_recovery_worker.py`, local HA evidence | Worker-loss/provider-ambiguity drill on target |
| Agent Governance | Tenant-scoped identity, kill switch, access review, delegation and tool-policy checks | Policy audit bridge tests; Phase C/E evidence | Deployed actor matrix and security review |
| Tenant Lifecycle | Suspend/deprovision transitions; child ordering; audit retention | Tenant/RBAC E2E; immutable audit retention evidence | Deployed Vendor/Reseller/Customer isolation acceptance |
| Celery/Workers | Explicit queues; stale sweep independent of execution redelivery | Worker/recovery tests; HA smoke | Production load and worker-loss drill |
| HA/Deployment | Deterministic bootstrap; restart recovery; portable Docker handling | Phase 14.10 local certification PASS | Target HA/recovery rehearsal |
| Certification | Exact SHA checkout/assertion and immutable evidence manifest | Workflow inspection; local certification | Exact final-SHA certification run |

## Combined release-critical gate

The release candidate is considered engineering-validated only when the following are green for the exact candidate SHA:

1. Backend regression tests.
2. AI Gateway durable-call fence regression.
3. Run Recovery and recovery-worker tests.
4. Tenant/RBAC real-stack isolation gate.
5. HA failure/recovery validation.
6. Production compose validation.
7. DAST ephemeral validation where the workflow is available.
8. Repository integrity checks: production completeness audit and diff check.

This document records engineering evidence only. It does not claim production deployment, external certification, live-provider acceptance, RPO/RTO achievement, or commercial acceptance.
