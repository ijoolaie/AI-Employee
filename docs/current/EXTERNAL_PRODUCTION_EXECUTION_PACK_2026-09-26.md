# External Production Execution Pack — 2026-09-26

## Purpose

This pack is the operator-facing execution sequence for closing the remaining **external production** gates after engineering and exact-release certification.

It does **not** certify the current `main` branch. It does not replace the exact-SHA certification of `v1.4.11`, and it does not permit evidence transfer between different SHAs.

### Current certification boundary

- Latest published/certified release: `v1.4.11`
- Exact certified SHA: `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Production Certification run: `35848311037`
- Certification job: `107139710452`
- Evidence artifact: `production-certification-evidence-v1.4.11-rc.1-90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Evidence SHA-256: `bfd75a37126bc3fcb98080d9f4a9522ae1d0c05ab05ca686f0be985f53334048`
- External production deployment: **PENDING**
- Commercial go-live: **PENDING**

The production target must be bound to an immutable accepted release identity before target evidence is collected.

---

## 1. Evidence rules

1. Every external result must identify:
   - target/environment;
   - execution timestamp in UTC;
   - operator/owner;
   - release tag and exact commit SHA deployed;
   - command/workflow used;
   - raw output or immutable artifact reference;
   - PASS/FAIL result.
2. Local, CI, rehearsal, or simulation evidence is supporting engineering evidence only.
3. Evidence from another SHA is not automatically transferable.
4. Documentation updates cannot substitute for operational evidence.
5. Secrets, credentials, tokens, private keys, customer data, and sensitive production payloads must not be committed to the repository or pasted into issue/PR text.
6. A failed gate is recorded as FAIL/PENDING with remediation; it is never converted to PASS by editing documentation.
7. Do not create a new release/tag as part of evidence collection unless the release process separately authorizes it.

---

## 2. Required target identity

Before deployment, capture:

```text
TARGET_NAME=
TARGET_ENVIRONMENT=production
DEPLOYED_RELEASE=v1.4.11
DEPLOYED_SHA=90dd5cbcfb0a372ee5d53b34f65868cd0acb181f
DEPLOYMENT_TIMESTAMP_UTC=
OPERATOR=
```

Also retain the deployment system's immutable image/container digest where available.

**PASS:** the running target can be demonstrated to correspond to the accepted release SHA.

**FAIL:** the target is running an unpinned/mutable branch, unknown revision, or a different unapproved SHA.

---

## 3. Gate sequence

Execute gates in this order. Do not skip a failed prerequisite.

| Gate | External evidence required | PASS condition | Owner |
|---|---|---|---|
| G0 Release identity | deployed tag/SHA + image digest | target matches accepted immutable release | Release/Platform |
| G1 Network/TLS | DNS, TLS, ingress/firewall, exposure evidence | intended public surface only; secure transport; no unintended DB/Redis exposure | Platform |
| G2 Secrets | secret-manager inventory + rotation/revocation/recovery evidence | production secrets are externalized and lifecycle-tested | Platform/Security |
| G3 Deployment/migrations | deployment log + migration result | deployment healthy and schema at expected revision | Platform |
| G4 Backup/restore | backup artifact + isolated restore + measured timings | restore succeeds and measured RPO/RTO meet approved targets | Platform/DBA |
| G5 SLO/SLI/alerts | baseline + dashboards + alert delivery | production measurements and alert routes are live | SRE |
| G6 Live providers | provider success/failure/retry/quota evidence | configured providers authenticate and failure modes are handled | Integration owner |
| G7 Runtime tenant/RBAC | Vendor/Reseller/Customer actor matrix | positive and negative authorization cases pass | Security/Product |
| G8 DAST | authenticated deployed-target scan + disposition/retest | findings remediated/accepted with evidence | Security |
| G9 HA/failure recovery | controlled target failure drill | recovery completes within approved RTO and data outcome is known | SRE |
| G10 Incident response | real alert → escalation → recovery drill | alert reaches named responders and recovery is demonstrated | SRE/Security |
| G11 On-call | named primary/backup + tested escalation | paging/escalation path works | Operations |
| G12 Data retention | deletion/archive/backup lifecycle evidence | retention policy is enforced and recoverability is understood | Operations |
| G13 Customer acceptance | customer-facing acceptance records | agreed acceptance scenarios pass | Product/Customer |
| G14 Commercial go-live | final release/provenance/approval record | all mandatory external gates are closed | Release owner |

---

## 4. G1 — Network / TLS / ingress

Run the repository engineering validation against the actual deployment configuration where applicable:

```bash
bash scripts/production_infrastructure_validation.sh
```

This is necessary but **not sufficient** for external certification.

Capture separately:

- DNS records and target;
- certificate chain and expiry;
- TLS configuration;
- ingress/load-balancer configuration;
- firewall/security-group rules;
- public ports;
- egress policy;
- database and Redis exposure;
- administrative access path;
- operator access/audit controls.

**PASS:** external exposure matches the approved architecture, HTTPS/TLS is valid, and stateful backend services are not unintentionally public.

---

## 5. G2 — Secrets lifecycle

Verify the production secret manager or deployment secret mechanism without exposing secret values.

Evidence must show:

- secret ownership;
- storage location/type;
- access policy;
- initial provisioning;
- rotation execution;
- revocation;
- recovery/restore procedure;
- application recovery after rotation where applicable.

The repository validation is supporting evidence only:

```bash
bash scripts/validate_production_secret_management.py
```

**PASS:** no production secret is sourced from Git, release artifacts, documentation, or plaintext deployment configuration, and rotation/revocation/recovery has been exercised against the real target.

---

## 6. G3 — Deployment and migration

Deploy only the approved immutable release.

Capture:

- deployment workflow/run;
- release tag;
- exact SHA;
- image digest if applicable;
- migration output;
- health checks;
- application/worker readiness;
- rollback reference.

Where applicable:

```bash
bash scripts/production_migrate.sh
```

**PASS:** all required services are healthy and the database is at the expected migration state with no competing migration head.

---

## 7. G4 — Backup / restore / RPO / RTO

The repository smoke test is useful as a prerequisite:

```bash
bash scripts/production_backup_restore_smoke.sh
```

External certification additionally requires a real target exercise.

Capture:

1. backup start/end time;
2. backup identifier and storage location;
3. encryption/protection status;
4. restore start/end time;
5. isolated restore target;
6. integrity/application verification;
7. measured RPO;
8. measured RTO;
9. data-loss assessment;
10. cleanup of temporary restore resources.

**PASS:** restore is independently verified and measured RPO/RTO satisfy the approved production objectives.

---

## 8. G5 — SLO / SLI / alerting

Establish the production baseline from real traffic/operations.

Capture at minimum:

- availability;
- API error rate;
- latency;
- worker/job health;
- database/Redis health;
- saturation/resource indicators;
- alert thresholds;
- alert destinations;
- acknowledgement/escalation evidence;
- error-budget calculation or approved equivalent.

**PASS:** metrics are sourced from the real target, alerts reach the intended responders, and the SLO/error-budget contract is operational rather than documentation-only.

---

## 9. G6 — Live providers and integrations

For every provider enabled for the production tenant, capture:

- provider identity;
- authentication success;
- one controlled successful transaction/request;
- timeout/failure behavior;
- retry/idempotency behavior;
- quota/rate-limit behavior;
- provider error observability;
- credential rotation/revocation behavior.

Do not record secret values.

**PASS:** each enabled production integration has successful and controlled failure evidence. Disabled providers must be explicitly recorded as disabled rather than silently treated as tested.

---

## 10. G7 — Vendor / Reseller / Customer runtime isolation and RBAC

Execute the external actor matrix defined in:

```text
docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md
```

At minimum capture positive and negative cases for:

### Vendor administrator

Allowed:
- own vendor control plane;
- permitted direct reseller administration.

Denied:
- unrelated reseller;
- customer tenant;
- unauthorized/non-admin vendor actions.

### Reseller administrator

Allowed:
- own reseller;
- permitted direct customer operations.

Denied:
- vendor control plane;
- unrelated reseller;
- unrelated customer.

Also verify:

- tenant context;
- API/UI parity;
- object read/write/delete isolation;
- order/invoice isolation;
- knowledge/file isolation;
- audit trail;
- delegated entitlement boundaries.

**PASS:** every required positive and negative case passes against the real deployed target.

---

## 11. G8 — Authenticated deployed-target DAST

Run an authenticated DAST scan against the deployed target, not only CI/local simulation.

Capture:

- scanner/version;
- target scope;
- authentication setup without exposing credentials;
- scan timestamp;
- raw report;
- findings;
- severity;
- disposition;
- remediation commits/issues;
- retest result.

**PASS:** all release-blocking findings are remediated or formally accepted by the authorized security owner, with retest evidence where remediation occurred.

---

## 12. G9 — HA / failure recovery

Run a controlled failure against the real target.

Examples may include only those explicitly approved by the target operations plan:

- application instance failure;
- worker failure;
- dependency restart;
- controlled node/service interruption.

Do not perform destructive tests outside the approved maintenance window.

Capture:

- failure start;
- affected component;
- detection time;
- recovery start;
- recovery completion;
- measured RTO;
- data integrity;
- duplicate/ambiguous work behavior;
- customer-visible impact;
- rollback/recovery action.

The repository rollback contract may be exercised as supporting evidence:

```bash
bash scripts/production_rollback_smoke.sh
```

**PASS:** the approved failure scenario recovers within target RTO and no unreconciled data or execution ambiguity remains.

---

## 13. G10 — Incident response

The repository simulation is not production evidence:

```bash
./scripts/incident_response_drill.sh
```

External evidence must demonstrate a real operational drill:

1. controlled alert/incident trigger;
2. alert delivery;
3. acknowledgement;
4. primary responder action;
5. backup escalation when applicable;
6. mitigation;
7. recovery;
8. customer/internal communication path;
9. incident timeline;
10. post-incident review/action items.

**PASS:** the complete alert-to-recovery chain works with named responders.

---

## 14. G11 — On-call ownership

Record:

- primary on-call owner;
- backup owner;
- escalation path;
- contact mechanism;
- coverage window;
- tested page/notification;
- acknowledgement time;
- escalation time.

**PASS:** a real test reaches the intended primary/backup path and escalation works.

---

## 15. G12 — Data retention / deletion / archive

Verify on the deployed target:

- customer deletion;
- archive behavior;
- retention periods;
- backup retention;
- restoration implications;
- audit-log retention;
- handling of deleted tenant data;
- scheduled cleanup where applicable.

**PASS:** behavior matches the approved retention policy and is evidenced against the actual target.

---

## 16. G13 — Customer acceptance

Execute the approved customer-facing acceptance scenarios for each enabled edition/tenant model.

At minimum include:

- login/authentication;
- tenant/workspace isolation;
- employee lifecycle;
- employee → run → AI → result;
- files → knowledge → memory;
- admin/developer controls;
- workflow/approval/schedule;
- relevant product/order/customer/invoice flows;
- localized EN/FA and RTL behavior where applicable.

Record customer/acceptance owner, date, environment, release SHA, scenario result, and unresolved issues.

**PASS:** all mandatory customer acceptance scenarios are explicitly accepted.

---

## 17. G14 — Final certification handoff

The final external certification package must contain:

```text
01-target-identity/
02-network-tls/
03-secrets/
04-deployment-migrations/
05-backup-restore-rpo-rto/
06-slo-sli-alerting/
07-live-providers/
08-runtime-isolation-rbac/
09-dast/
10-ha-recovery/
11-incident-response/
12-oncall/
13-data-retention/
14-customer-acceptance/
15-final-approval/
```

Every directory must contain evidence or an explicit signed/approved disposition.

The final manifest must include:

- accepted release tag;
- exact deployed SHA;
- image/container digest where applicable;
- target identity;
- execution timestamps;
- evidence hashes;
- gate results;
- exceptions/dispositions;
- approvers;
- final go/no-go authorization.

**External certification is PASS only when all mandatory gates are PASS or formally approved as non-blocking exceptions by the designated authority.**

---

## 18. Evidence naming convention

Use deterministic names:

```text
external-prod-<gate>-<target>-<YYYYMMDDTHHMMSSZ>.<ext>
```

Examples:

```text
external-prod-network-prod-20260926T120000Z.txt
external-prod-backup-restore-prod-20260926T130000Z.json
external-prod-dast-prod-20260926T140000Z.html
external-prod-rbac-prod-20260926T150000Z.json
```

Never put secrets in filenames, logs, screenshots, or evidence manifests.

---

## 19. Final state model

Use only these states:

- **PASS** — required evidence exists and acceptance criteria passed.
- **FAIL** — test executed and acceptance criteria failed.
- **PENDING EXTERNAL EXECUTION** — cannot yet be evaluated because the real target/test dependency is unavailable.
- **BLOCKED** — prerequisite or authorized access is missing.
- **WAIVED / ACCEPTED EXCEPTION** — explicitly approved by the designated authority with scope, rationale, expiry, and owner.

Do not use documentation-only evidence to convert **PENDING EXTERNAL EXECUTION** into PASS.

---

## 20. Current repository boundary

The following are already engineering-tested and should be reused as supporting evidence rather than reclassified as external production proof:

- clean local production-like certification;
- tenant isolation/RBAC/Knowledge;
- Employee → Run → AI → Result;
- Files → Knowledge → Memory;
- Admin/Developer;
- Workflow/Approval/Schedule;
- production configuration/security validation;
- CI certification workflows;
- local backup/restore and rollback rehearsals.

The remaining production-readiness gates require execution against the actual production target.

This pack is therefore an **execution plan and evidence contract**, not a production certification record.

---

## Related source documents

- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/current/PRODUCTION_SERVER_BASELINE.md`
- `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
- `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`
- `docs/current/COMMERCIAL_READINESS_AUDIT_2026-09-16.md`
- `docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md`
- `docs/current/PHASE_14_INCIDENT_RESPONSE_DRILL_EVIDENCE.md`
- `docs/current/PHASE_14_SLO_ERROR_BUDGET_ENGINEERING.md`
- `scripts/production_infrastructure_validation.sh`
- `scripts/production_backup_restore_smoke.sh`
- `scripts/production_rollback_smoke.sh`
- `scripts/production_migrate.sh`
- `scripts/incident_response_drill.sh`

**No release or tag is created by this pack.**
