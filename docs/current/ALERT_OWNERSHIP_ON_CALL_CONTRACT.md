# Alert Ownership & On-Call Contract

## Status

**Engineering contract implemented; external staffing and paging validation remain pending.**

## Ownership matrix

| Signal | Severity | Primary owner | Escalation | Evidence |
|---|---|---|---|---|
| API readiness loss | SEV-1 | platform-on-call | incident commander → service owner | alert event, acknowledgement, timeline |
| Database dependency failure | SEV-1 | platform-on-call | incident commander → data owner | dependency health, recovery timeline |
| Worker degradation | SEV-2 | platform-on-call | service owner | queue/worker health, timeline |
| Security event | SEV-1 | security-on-call | incident commander → security owner | alert, containment, audit evidence |

## Response objectives

These are engineering contract placeholders, not measured production SLAs:

- SEV-1 acknowledgement target: 5 minutes.
- SEV-1 incident owner assignment target: 10 minutes.
- SEV-2 acknowledgement target: 15 minutes.
- Escalate when the primary owner does not acknowledge within the target.

## Evidence contract

Every real alert exercise must capture alert ID, UTC timestamps, severity, owning rotation, acknowledgement, escalation, affected scope, release commit SHA, recovery action, and closure/post-incident review reference. Secret values must never be recorded.

## External boundary

A real production deployment must replace the logical roles above with named rotations, paging destinations, coverage windows, escalation contacts, and tested acknowledgement paths. This repository contract does not claim that a staffed on-call rotation or live paging integration exists.
