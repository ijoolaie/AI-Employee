# Phase 14.10 — External Production Certification & Customer Acceptance Evidence

Status: **EXTERNAL-PENDING**.

This document defines the final evidence gate for external production readiness. Repository and CI evidence may establish engineering readiness, but cannot substitute for independent production evidence, customer acceptance, or certification.

## Evidence gate

A release may be proposed for external production certification only when every applicable evidence item below is attached to the exact release identity.

| Evidence | Required record | Current boundary |
| --- | --- | --- |
| Exact release identity | Git commit SHA, tag/ref, edition/package checksums | Repository/release-process evidence |
| Deployment evidence | Target environment, deployment timestamp, deployed SHA, configuration identity | EXTERNAL-PENDING |
| Live provider validation | Provider/API checks performed against the deployed environment | EXTERNAL-PENDING |
| SLO evidence | Measured service/objective windows and error-budget results | EXTERNAL-PENDING |
| DR evidence | Backup cadence, restore drill, measured RPO/RTO and recovery timestamps | EXTERNAL-PENDING |
| Security/compliance evidence | Control results, review records and applicable independent attestations | EXTERNAL-PENDING |
| Customer acceptance | Named acceptance record, scope, date and accepted release identity | EXTERNAL-PENDING |
| Rollback readiness | Tested rollback target, procedure, owner and recovery decision | Engineering baseline + external verification pending |

## Required evidence package

For each candidate release, preserve a single evidence index containing:

1. exact Git SHA and release tag/ref;
2. immutable package checksums and edition manifests;
3. deployment record identifying environment and deployed SHA;
4. live provider validation results with timestamps;
5. measured SLO/error-budget window;
6. DR backup/restore drill with measured RPO/RTO;
7. security/compliance control evidence and reviewer identity;
8. customer acceptance record and accepted scope;
9. rollback rehearsal/readiness record; and
10. exceptions, unresolved risks and explicit disposition.

Evidence must be attributable, timestamped, reproducible where practical, and retained according to the applicable operational policy. Secrets, credentials, access tokens and unnecessary personal data must not be copied into the evidence package.

## Independent-evidence rule

CI, CodeQL, Architecture Guard, local Docker/runtime validation, repository tests, and generated release artifacts are engineering evidence. They do not prove external deployment, live third-party provider operation, measured production SLO attainment, customer acceptance, or independent certification.

The Phase 14.10 issue remains **EXTERNAL-PENDING** until the independent evidence listed above exists. Do not close the issue or label the product production-certified solely because repository gates are green.

## Certification decision

The final decision record should state one of:

- **ACCEPTED** — all required evidence is present and independently reviewed;
- **CONDITIONALLY ACCEPTED** — explicitly documented exceptions have owners and deadlines; or
- **REJECTED / DEFERRED** — one or more required evidence classes are missing or fail acceptance criteria.

A production claim must identify the exact accepted release identity and evidence package. Later commits are not covered automatically.
