# Production Certification Execution Pack

**Prepared:** 2026-09-05  
**Repository:** `ijoolaie/AI-Employee`  
**Current engineering main baseline:** `44e1c0f339e2440bafe9f4e122d2b63dc2fc09c2`  
**Purpose:** execute the remaining production/customer-readiness work without confusing repository evidence with real target-environment certification.

## Operating rule

Every P0 item must be attached to one immutable release identity. CI, local Docker, synthetic load, simulated providers, or documentation may establish engineering readiness but cannot close an external-environment gate.

Use `docs/current/PRODUCTION_EVIDENCE_INDEX.md` as the traceability index. Every evidence row must identify its evidence class and exact release SHA/tag; pending external gates must remain explicitly pending.

## Phase A — Freeze the release

1. Select the candidate commit from `main` after all engineering changes are merged.
2. Create an immutable release tag.
3. Record commit SHA, tag, container image digests, dependency lock identity, SBOM/provenance artifacts and configuration version.
4. Do not mutate the accepted release after external evidence collection starts.
5. If a remediation changes runtime behavior, create a new release identity and repeat affected evidence.

**Evidence:** release record + SHA/tag + image digests + checksums + provenance.

## Phase B — Deploy the real production target

Record:

- target environment and region;
- deployment timestamp;
- release SHA/tag;
- image digests;
- database migration version;
- TLS/ingress configuration;
- secret-store references (never secret values);
- PostgreSQL, Redis and object-storage endpoints/classes;
- health/readiness results;
- rollback target.

**Exit:** the exact accepted release is running and healthy on the real target.

## Phase C — Backup, restore and DR

Execute against the real target:

1. Verify scheduled encrypted PostgreSQL backup.
2. Verify object-storage versioning/lifecycle policy.
3. Capture backup timestamp and size/checksum.
4. Restore into an isolated recovery target.
5. Validate schema, representative records and tenant boundaries.
6. Exercise Redis recovery/rebuild behavior.
7. Measure elapsed restore time and establish observed RPO/RTO.
8. Record operator, timestamps, failures and remediation.

**Exit:** measured RPO/RTO meets the approved target or an explicit exception is signed.

## Phase D — Production SLO / SLI / error budget

Define and measure at minimum:

- availability;
- API latency (p50/p95/p99);
- error rate / 5xx rate;
- queue/job success and age;
- dependency/provider failure rate;
- recovery time;
- backup success rate.

Record the measurement window, traffic volume, alert thresholds, error-budget policy and owner. Do not claim an SLO from a short synthetic run alone.

## Phase E — Live provider validation

For every enabled production provider:

- successful authenticated request;
- timeout/retry behavior;
- quota/rate-limit behavior;
- provider error mapping;
- degraded dependency behavior;
- cost/usage accounting;
- recovery after transient failure.

Use production-safe test inputs and redact secrets/PII from evidence.

## Phase F — Vendor → Reseller → Client isolation/RBAC

Execute an ordered matrix on the running target:

| Actor / scope | Allowed | Must be denied |
|---|---|---|
| Vendor platform admin | platform-owned operations | client data outside authorized support scope |
| Reseller admin | reseller-owned tenants | sibling reseller/client tenants |
| Client admin | own tenant administration | other tenants/reseller/vendor resources |
| Client member | permitted client operations | admin-only operations and other tenants |
| Agent/worker | explicitly delegated run/tool scope | undelegated tools/resources |

Capture both positive and negative requests, tenant IDs, role/permission context, HTTP status and audit records. Close issue #19 only after this runtime evidence is attached.

## Phase G — DAST and independent security review

### DAST

A CI-only OWASP ZAP baseline scan is already implemented as engineering evidence. External closure still requires running-target DAST with authenticated/unauthenticated profiles as appropriate. Record scanner/version, target release, findings, severity, remediation and retest.

### Independent penetration test

Use an independent tester with a defined scope covering authentication, authorization/tenant isolation, API security, injection, secrets, file handling, tool execution, SSRF/network boundaries and relevant business-logic abuse. Record residual risk and formal disposition.

## Phase H — Networking and secrets

Verify:

- TLS certificate validity and minimum protocol/cipher policy;
- ingress exposure and firewall rules;
- private network placement for databases/queues where applicable;
- network policies/security groups;
- secret-store ownership;
- rotation without downtime where supported;
- credential recovery/revocation;
- no plaintext production secrets in repository, logs or artifacts.

The repository network-hardening and secret-management contracts are engineering-complete; external perimeter, secret-manager, rotation and recovery evidence is still required. Record references and configuration fingerprints, never secret values.

## Phase I — HA, failure recovery and incident response

Repository-level failure-recovery and incident-response engineering rehearsals are complete. External closure still requires controlled scenarios on the target architecture using the real recovery objectives and alerting path.

Run controlled failure scenarios:

1. API instance failure.
2. Worker failure during queued work.
3. Redis restart/failure.
4. PostgreSQL failover/recovery according to the target architecture.
5. Storage/dependency degradation.
6. Provider outage/timeout.

For each: inject failure, observe detection, measure recovery, verify data integrity and compare with the SLO/RTO target.

Then execute at least one incident-response exercise using the real alerting and escalation path. Record timeline, owner actions, communications, recovery and lessons learned.

## Phase J — Alert ownership and on-call

The repository routing contract is engineering-complete. External closure requires live monitoring and a tested owner/escalation path.

For each production alert, record:

- alert name and condition;
- severity;
- primary owner;
- backup/escalation owner;
- notification route;
- acknowledgement target;
- remediation runbook;
- test timestamp.

A passing alert rule without a tested owner/escalation path is not closure evidence.

## Phase K — P1 productization completion

The repository P1 engineering gates are reconciled. Remaining work in this phase is target verification/operational adoption where explicitly required, not an unresolved repository TODO list.

### Data retention/lifecycle

Map every retained data class to retention period, deletion/archive behavior, legal hold requirements where applicable, audit behavior and target verification.

The repository enforcement command is intentionally **dry-run by default**. Run `python -m scripts.enforce_retention --execute` only under an approved operational change when destructive enforcement is intended. Physical object deletion/version expiry and backup retention remain target/provider responsibilities.

### Human-in-the-loop TODO reconciliation

The approval-path documentation is reconciled: gated tool calls create an approval request and pause execution; explicit approval resumes the exact continuation; the worker re-checks authorization before continuing. There is no remaining claim in `run_service.py` that Human-in-the-loop is a future TODO.

### Documentation/evidence index

Keep `PRODUCTION_GAP_REGISTER_2026-09-04.md`, this execution pack, `PRODUCTION_EVIDENCE_INDEX.md` and the canonical status documents synchronized. Every completed gate must link to its evidence artifact and immutable release identity.

### Platform operations dashboard

The existing `/admin/operations` surface is the current engineering operational view. Target alerting, incident widgets and production adoption remain external/operational verification as applicable.

### Customer usage/budget/cost controls

Customer usage exposes budget utilization, remaining quota, unit cost and optimization guidance. Target billing/operations validation remains external where applicable.

### Cost anomaly detection/forecasting

Deterministic tenant-scoped daily anomaly detection and month-end projection are implemented with tests. Forecasts must expose the period and assumptions so they are decision support rather than false precision.

## Final acceptance sequence

1. Immutable release frozen.
2. Real target deployed.
3. Backup/DR and measured RPO/RTO passed.
4. SLO/SLI baseline established.
5. Live providers validated.
6. Vendor/Reseller/Client isolation and RBAC certified.
7. DAST remediated/retested.
8. Independent security review completed.
9. Network and secret lifecycle verified.
10. HA/failure and incident-response rehearsals completed.
11. On-call ownership/escalation tested.
12. Customer acceptance executed with exceptions explicitly recorded.

Only after the ordered sequence is complete should #210/#269 be closed and the project described as externally production-certified for the accepted scope.
