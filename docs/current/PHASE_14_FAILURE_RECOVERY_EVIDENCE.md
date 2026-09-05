# Phase 14 — Failure Recovery Engineering Evidence

Status: **implemented engineering baseline**.

This document records the repository-level failure-recovery rehearsal capability. It does not claim high availability or production failover certification.

## Scope

The CI smoke exercises the production-like Compose topology by:

1. verifying PostgreSQL, Redis, API, worker, beat, and frontend are running;
2. checking API health and dependency readiness;
3. restarting the API and re-checking health/readiness;
4. restarting worker and beat and verifying service recovery;
5. restarting Redis and PostgreSQL and verifying dependency readiness;
6. checking that Alembic still reports a current migration revision after dependency recovery; and
7. collecting service state/log evidence as a short-lived CI artifact.

The rehearsal is intentionally bounded. It tests restart/recovery behavior of a single production-like Compose instance; it does not establish multi-node HA, automatic failover, zonal redundancy, measured production RTO/RPO, or customer-serving resilience.

## Production certification boundary

The production certification plan still requires failure injection against the actual target architecture, measured recovery times, data-integrity verification, and an incident exercise using the real alerting/escalation path. PostgreSQL failover in particular must be exercised according to the target managed/cluster architecture rather than inferred from a container restart.

## Evidence handling

CI artifacts contain service state/logs and a checksum for the recovery smoke script. They are diagnostic engineering evidence and are retention-managed by CI. Durable production incident evidence belongs in the designated operational evidence store.
