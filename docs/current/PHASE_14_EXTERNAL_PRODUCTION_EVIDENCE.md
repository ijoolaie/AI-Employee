# Phase 14.10 — External Production Certification & Customer Acceptance Evidence

Status: **EXTERNAL-PENDING — INFRASTRUCTURE NOT YET AVAILABLE**.

## Current certified release candidate

- Release: `v1.3.8`
- Exact certified commit: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification run: `34052885700` — PASS
- Tag: `v1.3.8` → exact certified commit — VERIFIED
- Deployment checkpoint: Issue #343
- Deployment attempt: Run `34060615390` — failed during SSH configuration because required production Environment values were empty/missing.
- Remote deployment: **NOT EXECUTED**.

The certification result establishes a certified release candidate, not live production deployment or customer acceptance.

## Evidence gate

A release may be proposed for external production certification only when every applicable evidence item below is attached to the exact release identity.

| Evidence | Required record | Current boundary |
| --- | --- | --- |
| Exact release identity | Git commit SHA, tag/ref, edition/package checksums | **READY — v1.3.8** |
| Deployment evidence | Target environment, deployment timestamp, deployed SHA, configuration identity | **PENDING REAL TARGET** |
| Live provider validation | Provider/API checks against deployed environment | EXTERNAL-PENDING |
| SLO evidence | Measured service/objective windows and error-budget results | EXTERNAL-PENDING |
| DR evidence | Backup cadence, restore drill, measured RPO/RTO and recovery timestamps | EXTERNAL-PENDING |
| Security/compliance evidence | Control results, review records and applicable independent attestations | EXTERNAL-PENDING |
| Customer acceptance | Acceptance record, scope, date and accepted release identity | EXTERNAL-PENDING |
| Rollback readiness | Tested rollback target, procedure, owner and recovery decision | Engineering baseline + external verification pending |

## Required evidence package

For the exact `v1.3.8` identity, preserve a single evidence index containing:

1. exact Git SHA and release tag/ref;
2. immutable package checksums and edition manifests where applicable;
3. deployment record identifying environment and deployed SHA;
4. live provider validation results with timestamps;
5. measured SLO/error-budget window;
6. DR backup/restore drill with measured RPO/RTO;
7. security/compliance control evidence and reviewer identity;
8. customer acceptance record and accepted scope;
9. rollback rehearsal/readiness record; and
10. exceptions, unresolved risks and explicit disposition.

Evidence must be attributable, timestamped, reproducible where practical, and retained according to applicable operational policy. Secrets, credentials, access tokens and unnecessary personal data must not be copied into the evidence package.

## Independent-evidence rule

CI, CodeQL, Architecture Guard, local Docker/runtime validation, repository tests and generated release artifacts are engineering/release evidence. They do not prove external deployment, live third-party provider operation, measured production SLO attainment, customer acceptance or independent certification.

## Current decision boundary

The project is **release-certified but not production-deployed**. The next blocker is real infrastructure and protected deployment configuration. Missing production inputs must fail closed; they must never be invented or committed to the repository.

The Phase 14.10 gate remains **EXTERNAL-PENDING** until the independent evidence listed above exists. Do not close the gate or label the product externally production-certified solely because repository gates are green.

## Certification decision

The final decision record should state one of:

- **ACCEPTED** — all required evidence is present and independently reviewed;
- **CONDITIONALLY ACCEPTED** — explicitly documented exceptions have owners and deadlines; or
- **REJECTED / DEFERRED** — one or more required evidence classes are missing or fail acceptance criteria.

A production claim must identify the exact accepted release identity and evidence package. Later commits are not covered automatically.
