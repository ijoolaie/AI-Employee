# Phase 14 — Alert Ownership, Escalation & Routing

## Status

**Engineering contract implemented; live routing remains EXTERNAL-PENDING.**

The repository now contains a deterministic alert-routing contract for the two incident scenarios already exercised by the incident-response drill. The contract makes severity, logical owner, secondary escalation, acknowledgement target and external paging target explicit without storing provider credentials or real paging endpoints.

## Covered routes

| Alert | Scenario | Severity | Primary | Secondary | Ack target |
|---|---|---|---|---|---:|
| `api_readiness_loss` | `api-readiness-loss` | SEV-1 | `platform-on-call` | `platform-lead` | 10 min |
| `worker_degradation` | `worker-degradation` | SEV-2 | `platform-on-call` | `platform-lead` | 30 min |

The source of truth is `ops/alerting/alert-routing.yml`; `scripts/validate_alert_ownership_routing.py` validates the contract in CI and emits machine-readable engineering evidence.

## Evidence boundary

A passing CI contract proves that the repository has an explicit, internally consistent ownership/escalation model. It does **not** prove that a monitoring system emitted an alert, that a pager delivered it, that a human acknowledged it, or that escalation actually occurred within the stated target.

## External acceptance required

Before production certification, the logical placeholders must be bound to the deployed monitoring/paging system and tested with an operator-controlled target. The evidence package must include the deployed alert rule identity, real routing destination, named on-call rotation, acknowledgement/escalation timestamps, and incident timeline. No secrets should be committed to the repository.
