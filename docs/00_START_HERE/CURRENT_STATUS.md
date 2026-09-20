# Current Status

**Last reconciled:** 2026-09-20
**Latest published release:** `v1.4.7`
**Certified release SHA:** `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
**Exact-SHA Production Certification:** Run `35498984521` — PASS
**Certification job:** `106047204166` — PASS
**Product Gate failures:** `0`
**Current status:** v1.4.7 RELEASE-CERTIFIED / EXTERNAL PRODUCTION & COMMERCIAL ACCEPTANCE PENDING

## Current release

- Release: `v1.4.7`
- Exact certified SHA: `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Production Certification: PASS
- Frontend Playwright: 6/6 PASS
- Immutable certification evidence artifact: `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Evidence digest: `sha256:86c82af5326bce9d6be634df8779bf0a0f28ca16503ee34095786858780e1427`
- Production deployment claimed by certification: **false**
- Release assets: runtime package, four edition packages, edition manifest and SHA256SUMS published on the v1.4.7 GitHub release.

Certification applies only to the exact certified SHA. Later commits on `main` do not inherit release certification.

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a Human + Agent operating model. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The current engineering/release baseline is **v1.4.7 / `48a6df0...`**. Repository engineering, CI, production-like validation and exact-SHA Production Certification are complete for the tracked scope.

No evidence currently establishes real production deployment, live-provider operation, measured production SLO/DR, independent security review, staffed production operations or customer acceptance.

## Evidence boundary

CI, repository tests, local production-like validation, generated release artifacts and GitHub-hosted certification establish engineering/release evidence. They do not establish live production deployment, measured production SLO/DR, independent security review, customer acceptance or unrestricted commercial go-live.

Certification never transfers automatically across SHAs.

## Remaining external gates

1. Real production deployment and exact deployed-identity verification.
2. Live provider/payment/integration validation where applicable.
3. Production SLO/SLI and error-budget measurements.
4. Real backup/restore and measured DR RPO/RTO.
5. Vendor → Reseller → Client runtime isolation/RBAC evidence on the real target.
6. Authenticated DAST against the running target.
7. Independent penetration/security review.
8. Production networking/TLS and secret-manager lifecycle evidence.
9. HA/failure-recovery and rollback rehearsal.
10. Incident-response and staffed on-call evidence.
11. Vendor → Reseller → Customer acceptance in order.
12. Final residual-risk disposition and commercial go-live gate.

These external gates are tracked by issues #210, #269 and #19.

Broad feature expansion is not the default next step unless external validation identifies a concrete engineering defect.

## Historical releases

- `v1.4.6` remains immutable at its certified SHA `f3d6003...`.
- Historical `v1.4.5` remains immutable and is not the current certified release.
- Earlier RC/candidate documentation is historical evidence only.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history, GitHub issues, documentation or chat. Missing required production inputs must fail closed.
