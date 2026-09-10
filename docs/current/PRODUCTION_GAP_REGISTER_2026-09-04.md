# Production & Productization Gap Register

**Reconciled:** 2026-09-10  
**Repository:** `ijoolaie/AI-Employee`  
**Current engineering mainline:** `decde0ad333ba972a79053b3da6489f92a2648de`

## Operating constraint

The application has a certified release-candidate state, but the project does not currently have a configured real production target. Post-`v1.3.8` engineering hardening has continued on mainline; that newer mainline is not certified until a new immutable release identity receives fresh certification.

Real production deployment, live provider behavior, measured target SLO/RPO/RTO, target network/secret lifecycle, independent penetration testing and customer acceptance remain blocked until the required external environment/access exists.

## Certified release checkpoint

- Release candidate: `v1.3.8`
- Exact certified commit: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification run: `34052885700` — PASS
- Tag identity: VERIFIED
- Deployment attempt: `34060615390` — FAIL at SSH configuration before remote deployment
- Deployment checkpoint: Issue #343
- Current mainline: `decde0ad333ba972a79053b3da6489f92a2648de` — NOT CERTIFIED

## Post-release engineering hardening

The current mainline includes merged hardening for Stripe Customer identity/idempotency, Subscription initialization, Shopify webhook registration and sync, PaymentRefund, webhook delivery, customer upsert, Stripe Customer concurrency, OnboardingProgress, transactional outbox enqueue, tenant/RBAC bootstrap, refund lifecycle BillingEvent, BillingEvent `record_event()` and concurrent RAG indexing.

Open engineering hardening at reconciliation time:

- PR #423 / Issue #422 — NULL-safe `TeamInstallation` scope uniqueness using PostgreSQL partial unique indexes.

These changes are engineering evidence, not inherited certification evidence.

## P1 completion status

| ID | Gap | Current state |
|---|---|---|
| 7.15 | Data retention & lifecycle enforcement | **ENGINEERING IMPLEMENTED** — tenant-scoped retention service + tests + policy documentation. |
| 7.16 | Human-in-the-loop TODO reconciliation | **ENGINEERING COMPLETE**. |
| 7.17 | Documentation consolidation & evidence index | **IN PROGRESS — current-main reconciliation pass**. |
| 7.18 | Platform operations dashboard | **ENGINEERING COMPLETE** — existing `/admin/operations` surface. |
| 7.19 | Customer usage, budget & cost controls | **ENGINEERING IMPLEMENTED**. |
| 7.20 | Cost anomaly detection & forecasting | **ENGINEERING IMPLEMENTED**. |

## Recently reconciled engineering evidence

- **Production certification:** Run `34052885700` passed the complete production-like certification suite for exact commit `fd1e74b...`.
- **Marketplace reliability:** critical Marketplace Playwright flow passed after selector correction for shortened installation IDs.
- **Immutable release identity:** `v1.3.8` tag resolves to the exact certified commit.
- **Controlled deployment:** Run `34060615390` accepted `v1.3.8` and `DEPLOY` but stopped in SSH configuration because required production Environment values were empty/missing. No remote deploy step executed.
- **SLO/error budget:** engineering contract complete; live measurement remains external.
- **Provider integration:** preflight complete; live provider authentication/transactions/webhooks remain external.
- **Runtime isolation/RBAC:** dedicated real-stack CI gate complete; external actor-matrix certification remains external.
- **Production network hardening:** engineering contract complete; real firewall/security-group/WAF/TLS/egress evidence remains external.
- **Production secret management:** engineering contract complete; external manager/rotation/recovery evidence remains external.
- **Mainline reliability:** post-`v1.3.8` concurrency and side-effect hardening is substantially advanced, but requires a new release certification.

## What remains P0 / external

1. Provision a real production target.
2. Configure protected production Environment inputs without exposing secret values.
3. Promote a deliberately selected immutable release SHA and deploy that exact identity.
4. Verify deployed identity and service health.
5. Real backup/restore/DR with measured RPO/RTO.
6. Production SLO/SLI and error-budget measurement.
7. Live provider credentials/endpoints and failure-mode validation.
8. Vendor → Reseller → Client runtime isolation/RBAC certification.
9. DAST against an authenticated deployed target.
10. Independent penetration test/security review.
11. Production networking hardening evidence.
12. External secret management, rotation and recovery rehearsal.
13. HA/failure-recovery rehearsal against target RTO.
14. Executed incident-response drill.
15. Named alert ownership/on-call escalation and routing test.
16. Final external certification/customer acceptance (#210/#269).

## Engineering exit before next release candidate

Before promoting the current mainline into a new release candidate:

1. Merge and certify PR #423 if its invariant fix remains valid after final review.
2. Complete the systematic execution and side-effect boundary audit.
3. Verify database migration graph and release manifest against the actual mainline.
4. Reconcile canonical status, roadmap, versioning and evidence documents to the exact selected SHA.
5. Run the full required release gate topology on that exact HEAD.
6. Create the immutable release identity only after the above evidence is green.

## Acceptance rule

Local, CI, simulated and synthetic evidence cannot substitute for an external production gate. Every external record must be attached to the exact immutable release identity accepted for production. Do not place secrets in GitHub issues, commits, documentation or chat.
