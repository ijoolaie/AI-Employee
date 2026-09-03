# Phase 13.5 — Agent Observability

## Goal
Instrument the Agent Runtime so every execution has tenant-safe, correlated lifecycle evidence without recording prompts, model output, tool arguments, secrets, or memory payloads.

## Contract

Every runtime execution should expose:

- stable `run_id`, `tenant_id`, `employee_id`, and `employee_version_id` correlation;
- lifecycle events: `received`, `running`, `succeeded`, `failed`;
- duration and terminal outcome;
- timeout and retry outcome, including attempt number and whether retry was allowed;
- approval state and approval identifier when applicable, without approval payloads;
- tool-call name and outcome only, never tool arguments or returned sensitive payloads;
- bounded memory count/provenance metadata only, never memory text or embeddings;
- failure category suitable for aggregate dashboards.

## Safety requirements

1. Never put prompts, model responses, tool arguments/results, tokens, credentials, authorization headers, or memory contents into telemetry attributes.
2. Tenant identifiers may be used for correlation but must not be emitted into cross-tenant aggregate labels with unbounded cardinality.
3. Runtime evidence must remain additive: observability failure must not turn a successful task into a failed task.
4. Retries and timeouts must be distinguishable from ordinary failures.
5. Approval correlation must use the exact run/tool-call identity already enforced by Phase 13.3.

## Acceptance criteria

- Agent Runtime emits lifecycle spans with stable correlation fields.
- Timeout/retry decisions are observable.
- Approval and tool-call outcomes are correlated without sensitive payloads.
- Memory provenance is observable only as bounded metadata.
- Regression tests prove sensitive values are excluded and tenant context is preserved.
- Existing Run execution behavior remains unchanged when telemetry is unavailable.

## Sequencing

Phase 13.4 is merged before this phase. Phase 13.5 is implemented as a separate PR and must pass CI, Architecture Guard, CodeQL, Production Observability, and Production Rollback & Alerting before merge.

Green CI is engineering evidence only; it is not external production acceptance.
