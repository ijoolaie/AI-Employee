# External Production Execution Plan — v1.4.1

**Status:** READY FOR EXTERNAL EXECUTION

**Release:** `v1.4.1`

**Exact release SHA:** `f7f5062feb125c7ca50263f74a0e40bc4abfa591`

**Engineering certification:** PASS — Production Certification run `34696339261`, job `103560364112`

**Scope:** Convert the current engineering-certified release into environment-specific external production evidence without transferring certification across SHAs.

## Non-negotiable release boundary

All external evidence in this execution must reference exactly:

- release tag: `v1.4.1`
- source SHA: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`

If production changes require a new source commit, stop, create a new release candidate, run fresh exact-SHA Production Certification, and use that new immutable identity for subsequent evidence.

## Phase 0 — External execution readiness

**Goal:** prepare the real target and evidence owners before deployment.

- [ ] Production target selected (VPS/server/cloud)
- [ ] Public DNS name selected
- [ ] TLS certificate path selected
- [ ] Firewall/security groups configured
- [ ] SSH/operator access established
- [ ] PostgreSQL storage and backup destination prepared
- [ ] Redis storage prepared
- [ ] Secret-management mechanism selected
- [ ] Monitoring/alert destination selected
- [ ] Incident owner and escalation path assigned
- [ ] Independent security reviewer/tester identified
- [ ] Provider credentials/production integrations identified

**Exit evidence:** target identity, operator identity, network/security checklist, secret-manager ownership, monitoring ownership.

## Phase 1 — Immutable release and artifact reconciliation

**Goal:** establish the exact artifact set that may be deployed.

- [x] `v1.4.1` published
- [x] Exact target SHA verified
- [x] Runtime artifact published
- [x] Vendor artifact published
- [x] Self-Hosted artifact published
- [x] Reseller artifact published
- [x] Customer artifact published
- [x] `EDITION-RELEASE-MANIFEST.json` published
- [x] `SHA256SUMS` published
- [ ] External operator independently records downloaded artifact checksums
- [ ] Migration head recorded from the exact release

**Exit evidence:** signed/recorded release identity, artifact checksums, migration identity/head.

## Phase 2 — Vendor production deployment

**Goal:** establish the authoritative control-plane environment first.

- [ ] Deploy exact `v1.4.1` artifacts
- [ ] Verify deployed source/artifact identity
- [ ] Configure production secrets externally
- [ ] Run migration and record resulting head
- [ ] Verify API/frontend health
- [ ] Verify TLS, CORS, trusted-host and debug posture
- [ ] Verify backup creation and restoration path
- [ ] Verify monitoring and alerts
- [ ] Execute Vendor RBAC/authority acceptance matrix
- [ ] Capture negative-path authorization evidence

**Exit evidence:** Vendor deployment record + health + migration + backup/recovery + security + RBAC evidence.

## Phase 3 — Reseller production deployment

**Goal:** validate delegated operation without Vendor-global authority.

- [ ] Provision through the accepted Vendor path
- [ ] Deploy exact approved Reseller artifact
- [ ] Verify artifact/source identity
- [ ] Configure reseller-owned secrets only
- [ ] Validate quota/entitlement ceilings
- [ ] Validate customer provisioning path
- [ ] Validate monitoring/backups
- [ ] Execute Reseller RBAC/authority acceptance matrix
- [ ] Capture negative-path authorization evidence

**Exit evidence:** Reseller deployment record + delegation + RBAC/isolation evidence.

## Phase 4 — Customer production deployment

**Goal:** validate customer isolation and least privilege.

- [ ] Provision through authorized upstream path
- [ ] Deploy exact approved Customer artifact
- [ ] Verify artifact/source identity
- [ ] Configure customer-owned secrets
- [ ] Validate tenant isolation
- [ ] Validate customer RBAC and entitlements
- [ ] Validate monitoring/backups
- [ ] Execute Customer acceptance matrix
- [ ] Capture negative-path authorization/isolation evidence

**Exit evidence:** Customer deployment record + tenant-isolation + RBAC evidence.

## Phase 5 — Live integrations and operational SLO

**Goal:** replace simulated/engineering evidence with measured target evidence.

- [ ] Live AI provider validated where applicable
- [ ] Live email validated where applicable
- [ ] Live payment/commerce/WhatsApp integrations validated where applicable
- [ ] Availability SLI measured
- [ ] Latency SLI measured
- [ ] Error-rate SLI measured
- [ ] WorkItem/Agent success SLI measured
- [ ] Error budget defined and observed
- [ ] Alert thresholds tested

**Exit evidence:** timestamped production measurements and alert test records.

## Phase 6 — Backup, DR, HA and rollback

**Goal:** demonstrate recoverability on the real target.

- [ ] Backup completed before destructive testing
- [ ] Restore drill executed
- [ ] Measured RPO recorded
- [ ] Measured RTO recorded
- [ ] Failure/recovery rehearsal executed
- [ ] HA behavior validated where HA is deployed
- [ ] Rollback to the previous known-good release rehearsed
- [ ] Recovery artifact identity recorded

**Exit evidence:** drill report with timestamps, measured RPO/RTO, outcome and corrective actions.

## Phase 7 — Security and perimeter evidence

**Goal:** validate the deployed attack surface independently.

- [ ] TLS/perimeter hardening evidence
- [ ] Secret rotation/recovery evidence
- [ ] DAST against running target
- [ ] Dependency/container vulnerability review
- [ ] Independent penetration test/security review
- [ ] Findings triaged and remediated or accepted with documented exception

**Exit evidence:** scanner reports, independent review report, findings disposition.

## Phase 8 — Incident response and acceptance

**Goal:** prove operational ownership and ordered acceptance.

- [ ] Incident drill executed
- [ ] Detection-to-escalation timing recorded
- [ ] On-call ownership demonstrated
- [ ] Rollback/recovery decision path exercised
- [ ] Vendor acceptance recorded
- [ ] Reseller acceptance recorded after Vendor acceptance
- [ ] Customer acceptance recorded after Reseller acceptance
- [ ] Final exceptions/risks dispositioned

**Exit evidence:** incident drill record, on-call evidence, ordered acceptance records, final risk register.

## Final gate

Close the external-production gate only when every required evidence item is attached to this exact release identity and independently reconciled.

Engineering CI, local Docker, production-like GitHub Actions, simulated providers, and local RBAC tests remain supporting evidence; they are not substitutes for real-target evidence.
