# Production & Productization Gap Register

**Reconciled:** 2026-09-05
**Repository:** `ijoolaie/AI-Employee`

## Operating constraint

The current execution environment is limited to GitHub and the developer's local machine. This cycle closes repository-verifiable work only. Real production deployment, live provider behavior, measured target SLO/RPO/RTO, target network/secret lifecycle, independent penetration testing and customer acceptance remain blocked until the required external environment/access exists.

## P1 completion status

| ID | Gap | Current state |
|---|---|---|
| 7.15 | Data retention & lifecycle enforcement | **ENGINEERING IMPLEMENTED** — tenant-scoped retention service + tenant-wide runner + tests + policy documentation. Target scheduler/object-storage/backup verification remains external. |
| 7.16 | Human-in-the-loop TODO reconciliation | **ENGINEERING COMPLETE** — approval pause/resume behavior documented accurately. |
| 7.17 | Documentation consolidation & evidence index | **ENGINEERING COMPLETE** — canonical status/gap/production execution docs reconciled. |
| 7.18 | Platform operations dashboard | **ENGINEERING COMPLETE** — existing `/admin/operations` metrics/dead-letter surface confirmed; target alerting/incident widgets remain external. |
| 7.19 | Customer usage, budget & cost controls | **ENGINEERING IMPLEMENTED** — customer usage exposes budget utilization, remaining quota, unit cost and optimization guidance. |
| 7.20 | Cost anomaly detection & forecasting | **ENGINEERING IMPLEMENTED** — deterministic tenant-scoped daily anomaly detection and month-end projection with tests. |

## Recently reconciled engineering evidence

- **SLO/error budget:** PR #324 establishes deterministic engineering objectives, synthetic observations, error-budget calculations and an explicit non-production certification boundary. Live SLO/SLI measurement remains external.
- **Provider integration:** PR #325 establishes deterministic Stripe/Shopify integration preflight coverage and enumerates the live operations requiring external credentials/endpoints. Live provider authentication, transactions and webhook delivery remain external.
- **Immutable release evidence:** PR #320 builds API/frontend images from the exact release SHA in CI, captures local image identities, generates CycloneDX SBOMs and records CI build metadata. External registry publication, signed attestations and production release acceptance remain external.
- **Alert ownership/routing:** PR #327 establishes deterministic severity, primary/secondary ownership and acknowledgement targets for the incident scenarios. Live paging, staffed on-call coverage and human escalation remain external.
- **Runtime isolation/RBAC:** PR #329 establishes a dedicated real-stack CI gate for Vendor/Reseller/Customer tenant isolation, negative authorization paths and RBAC enforcement. External actor-matrix certification remains external.
- **Production network hardening:** the new network-hardening contract validates that the production compose topology publishes no host ports, keeps services on the private backend network, uses loopback health checks, and enables fail-closed rate limiting. Real firewall/security-group/WAF/TLS/egress evidence remains external.

## Retention policy

The default retention window is 365 days, bounded to 1–3650 days when explicitly configured. Audit logs and usage events older than the cutoff are removed for the selected tenant. Terminal employee-memory rows (`expired`, `deleted`, `superseded`) older than the cutoff are removed. Stale active file metadata is soft-deleted with `deleted_at`; physical object deletion remains the responsibility of the storage-provider lifecycle policy. See `docs/current/31_DATA_RETENTION_LIFECYCLE.md`.

## DAST engineering evidence

A repeatable CI-only OWASP ZAP baseline scan is now implemented against the ephemeral production-like API stack. The validation builds and starts the production compose topology, waits for the live API target, runs the baseline scan, and uploads JSON/HTML evidence as a short-retention workflow artifact. The successful validation is engineering evidence only; authenticated DAST against the deployed production/staging target and an independent penetration test remain external gates.

## What remains P0 / external

1. Immutable production release publication with an external registry digest, signed SBOM/provenance and accepted production release identity.
2. Deployment to a real production/staging target.
3. Real backup/restore/DR with measured RPO/RTO.
4. Production SLO/SLI and error-budget measurement.
5. Live provider credentials/endpoints and failure-mode validation.
6. Vendor → Reseller → Client runtime isolation/RBAC certification.
7. DAST against an authenticated deployed target.
8. Independent penetration test/security review.
9. Production networking hardening evidence.
10. External secret management, rotation and recovery rehearsal.
11. HA/failure-recovery rehearsal against target RTO.
12. Executed incident-response drill.
13. Named alert ownership/on-call escalation and routing test.
14. Final external certification/customer acceptance (#210/#269).

## Acceptance rule

Local, CI, simulated and synthetic evidence cannot substitute for an external production gate. Every external record must be attached to the exact immutable release identity accepted for production. Do not place secrets in GitHub issues, commits, documentation or chat.
