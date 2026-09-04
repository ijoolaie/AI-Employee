# Phase 14.9 — Incident Response & Operational Readiness

Status: **implemented engineering baseline**.

This runbook defines incident taxonomy, severity, ownership, response flow, rollback/recovery, evidence capture and exercise boundaries. It does not claim that a real incident has occurred or that production certification has been achieved.

## Incident taxonomy

Classify the primary failure mode before selecting a response path:

| Class | Examples | First response focus |
| --- | --- | --- |
| Availability | API/worker outage, queue stall, database unavailable | stabilize service, protect data, restore capacity |
| Correctness | duplicate execution, lost state, inconsistent workflow result | stop unsafe processing, preserve evidence, reconcile state |
| Isolation / Authorization | cross-tenant access, RBAC bypass, scope violation | contain immediately, disable affected path, preserve audit evidence |
| Security / Secrets | exposed credential, suspicious access, malicious input | contain access, rotate/revoke affected secrets, preserve forensic evidence |
| Data / Recovery | corruption, failed migration, restore failure | freeze destructive changes, select verified recovery point |
| Performance / Capacity | saturation, latency regression, resource exhaustion | apply backpressure, shed non-critical load, restore headroom |
| Release / Configuration | bad deploy, incompatible config, artifact mismatch | stop rollout, identify exact release identity, rollback application first |
| Dependency / Provider | external API outage, provider degradation, credential rejection | isolate provider failure, use bounded retry/fallback, avoid retry storms |

## Severity model

| Severity | Trigger | Response target | Escalation |
| --- | --- | --- | --- |
| SEV-1 | Active security/isolation breach, material data loss, or broad service outage | immediate containment; incident lead engaged now | engineering + security/owner leadership |
| SEV-2 | Major customer-facing degradation, repeated unsafe execution, or critical workflow failure | rapid triage and mitigation | service owner + engineering lead |
| SEV-3 | Limited degradation with workaround or isolated component failure | scheduled response with active tracking | component owner |
| SEV-4 | Minor defect, alert noise, documentation/configuration issue | backlog or routine operational work | owning team |

Severity may be raised at any time when scope, customer impact, data risk or security confidence worsens.

## Ownership boundaries

- **Incident lead:** coordinates severity, decisions, timeline, escalation and closure.
- **Service/component owner:** executes technical diagnosis and mitigation for the affected subsystem.
- **Security owner:** leads security/isolation/secrets incidents and decides containment/credential actions.
- **Data/recovery owner:** leads restore, migration reconciliation and recovery-point selection.
- **Release owner:** owns deployment identity, rollback/cutover decisions and artifact integrity.
- **Communications owner:** records stakeholder/customer updates when required by the operating process.

The incident lead may delegate execution but retains decision accountability until handoff is explicitly recorded.

## Standard response flow

1. **Detect and declare:** record detection time, alert/source, suspected class and initial severity.
2. **Assign ownership:** name incident lead and relevant technical owners.
3. **Contain:** stop unsafe writes/executions, isolate affected tenants/components, or disable the failing release/path as appropriate.
4. **Preserve evidence:** capture logs, metrics, traces, audit records, release SHA, migration revision, queue state and relevant configuration identifiers without copying secrets.
5. **Diagnose:** establish impact scope and distinguish symptoms from root cause.
6. **Mitigate:** choose the least destructive reversible action first.
7. **Recover:** restore service/data using the appropriate recovery runbook and validate authorization, tenant isolation, workers and data integrity before cutover.
8. **Communicate:** record material status changes, decisions, owner changes and customer-impact statements.
9. **Verify closure:** confirm monitoring health and absence of continuing unsafe behavior.
10. **Close and learn:** record timeline, root cause, contributing factors, corrective actions and evidence references.

## Rollback and recovery decision rules

- Prefer application rollback to a known-good commit/build when the application release is the fault domain.
- Do not casually downgrade production database migrations; use the Phase 14.6 forward-first migration/recovery strategy.
- For suspected authorization or tenant-isolation failure, containment takes priority over availability. Disable the affected operation/path before attempting broad recovery.
- For secret exposure, revoke/rotate the affected credential through the secret-management process and do not place the secret in tickets, logs, commits or artifacts.
- For data corruption, preserve the original evidence and select a verified recovery point before modifying the active database.
- Do not declare recovery complete until health, authorization, worker and data-integrity checks pass.

See the Phase 14.6 recovery runbook for backup integrity, isolated restore and RPO/RTO evidence requirements.

## Evidence capture contract

Every declared incident or exercise should capture, at minimum:

- incident identifier;
- severity and classification;
- detection/declaration/recovery/closure timestamps;
- incident lead and technical owners;
- affected service, tenant scope and customer-impact statement (if applicable);
- exact application/release commit SHA;
- database migration revision when relevant;
- relevant alert, metric, log and audit references;
- actions and decision rationale;
- rollback/recovery procedure used;
- validation results and remaining risk;
- follow-up actions with owners and due dates.

Evidence must be sanitized: never copy passwords, API keys, access tokens, private keys or other secret material into incident records.

## Operational exercises

Run tabletop or technical recovery exercises for representative failure modes, including at least:

1. worker/queue outage or redelivery storm;
2. authorization/tenant-isolation regression;
3. bad application release and rollback;
4. database backup restore and migration mismatch;
5. provider/dependency degradation;
6. secret exposure containment.

An exercise record must identify that it is an **exercise**, include the scenario and expected outcome, record observed actions/timing, attach non-secret evidence references, and list gaps. Exercise evidence must never be represented as evidence that a real production incident occurred.

## Closure and post-incident review

A SEV-1/SEV-2 incident should receive a documented review covering timeline, root cause, contributing conditions, detection quality, response effectiveness, customer impact, control failures and corrective actions. Corrective actions should be tracked to completion or explicitly accepted as residual risk.

## Evidence boundary

This document establishes an operational-readiness contract and runbook. Repository tests can verify that required runbook sections remain present; they cannot prove production response performance. Production readiness still requires deployment-specific evidence, measured exercises, real ownership/contacts and any applicable external/customer acceptance evidence.
