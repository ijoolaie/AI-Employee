# Phase 14 — SLO / SLI / Error Budget Engineering Baseline

## Status

**Engineering contract implemented; external production measurement pending.**

The repository already exposes aggregate Prometheus signals for HTTP requests and latency, workflow execution, Celery tasks, dependency health, and SLO outcomes. This document defines the planning contract that consumes those signals.

## Planning objectives

| Objective | Target | Planning window |
|---|---:|---:|
| API availability | >= 99.5% | 30 days |
| API HTTP 5xx rate | <= 0.5% | 30 days |
| API latency objective | >= 95% within the selected p95 threshold | 30 days |

These are engineering planning targets, not contractual customer SLAs.

## Error budget

For availability, the allowed failure ratio is `1 - 0.995 = 0.5%` per 30-day window. The remaining budget is computed from the observed success ratio against that allowance.

For HTTP 5xx, the allowed error ratio is `0.5%`. The remaining budget is the unused portion of that allowance.

The CI validator uses deterministic synthetic observations solely to verify the formulas and evidence shape. It does not measure real traffic.

## SLI rules

- Availability SLI: successful eligible API requests divided by eligible API requests.
- Error-rate SLI: HTTP 5xx responses divided by eligible API requests.
- Latency SLI: proportion of eligible API requests within the selected latency threshold; production monitoring must retain the underlying histogram/time-series needed to calculate the agreed percentile.
- Exclude health-check noise only through an explicitly documented eligibility rule; never silently remove customer-serving failures.
- Keep Prometheus labels aggregate-only and avoid tenant/user identifiers to prevent cardinality and privacy leakage.

## Error-budget policy

When a production window consumes the budget faster than the agreed burn-rate policy, freeze discretionary reliability-risking releases and prioritize remediation. A release may proceed only when the release gate's defined burn-rate policy permits it and the evidence is attached to the same immutable release identity.

## External measurement still required

Production certification requires a real monitoring target, real traffic volume, measurement window, actual SLI values, burn-rate/error-budget history, alert routing, named ownership, and reconciliation to the immutable production release. CI and synthetic evidence cannot close that gate.
