# Production Readiness Status

**Status date:** 2026-09-20
**Latest published release:** `v1.4.7`
**Exact certified release SHA:** `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
**Production Certification run:** `35498984521` — PASS
**Certification job:** `106047204166` — PASS
**Product Gate failures:** `0`
**Current status:** ENGINEERING/RELEASE CERTIFIED / EXTERNAL PRODUCTION & COMMERCIAL ACCEPTANCE PENDING

## Current release boundary

### v1.4.7

- Exact certified SHA: `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Exact-SHA checkout/assertion: PASS
- Backend/frontend/DB certification stages: PASS
- Product Gates: 0 failures
- Frontend Playwright: 6/6 PASS
- Certification evidence artifact: `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Production deployment claimed: **false**

Certification applies only to the exact v1.4.7 SHA. Later commits do not inherit it.

## Engineering evidence complete

- Backend and frontend validation.
- Database migration and single-head checks.
- Auth, RBAC and tenant-isolation gates.
- Conversation isolation.
- Employee → Run → AI → Result.
- Files → Knowledge → Memory.
- Workflow → Approval → Schedule.
- Orders → Sales → Invoice → Billing.
- Unified WorkItem Human and Agent.
- Production-like infrastructure/readiness.
- OCR runtime/extraction.
- Dependency E2E.
- Product gates and frontend Playwright.
- Release artifact generation and checksum validation.

## External launch blockers

| Area | Status | Required evidence |
|---|---|---|
| Real production deployment | 🔴 | Exact frozen release identity running on approved target |
| Backup/restore + DR | 🔴 | Real backup, isolated restore, measured RPO/RTO |
| Production SLO/SLI | 🔴 | Real target measurements, alerts and error-budget baseline |
| Live providers | 🔴 | Provider authentication and success/failure/retry/quota validation |
| Vendor → Reseller → Client isolation | 🔴 | Runtime actor matrix on deployed target |
| DAST | 🔴 | Authenticated deployed-target scan + remediation/retest |
| Independent security review | 🔴 | Independent pentest/security evidence |
| Network hardening | 🔴 | TLS/firewall/ingress/egress/perimeter evidence |
| Secret lifecycle | 🔴 | Secret manager, rotation, revocation and recovery evidence |
| HA/failure recovery | 🔴 | Controlled target failure rehearsal against RTO |
| Incident response | 🔴 | Real alert-to-recovery drill |
| On-call | 🔴 | Named primary/backup ownership and tested escalation |
| Vendor/Reseller acceptance | 🔴 | Completed acceptance evidence |
| Customer acceptance | 🔴 | Completed launch-scope acceptance |

## Final acceptance sequence

1. Freeze/accept v1.4.7 for external deployment.
2. Provision and harden the approved production target.
3. Deploy the exact frozen release identity.
4. Verify deployment, image and migration identity/checksums.
5. Validate networking and secret-management lifecycle.
6. Validate live providers.
7. Establish production SLI/SLO/error budget.
8. Execute backup/restore and measure RPO/RTO.
9. Certify deployed Vendor/Reseller/Client isolation and RBAC.
10. Run DAST and independent security review.
11. Rehearse HA/failure recovery and rollback.
12. Execute incident-response/on-call drill.
13. Complete Vendor/Reseller/Customer acceptance.
14. Reconcile exceptions/residual risks.
15. Run the final commercial go-live gate.

Until that sequence is complete, the product should be described as **engineering/release certified with external production/commercial gates pending**, not as externally production-certified.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history, GitHub issues, documentation or chat. Missing required production inputs must fail closed.
