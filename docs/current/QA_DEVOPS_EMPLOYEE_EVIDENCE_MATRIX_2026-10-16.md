# QA & DevOps Employee Evidence Matrix — 2026-10-16

## Scope and evidence rules

This checkpoint maps the `ai_qa_devops` role contract to registered tools, its semantic handler, and existing repository evidence. A QA/DevOps artifact is not proof that a repository, CI service, monitoring platform, incident system, or deployment provider was queried. A deployment/rollback proposal is not an executed change.

Evidence labels: **Artifact-backed** = a tenant-scoped artifact/result is persisted; **CI/source evidence** = repository implementation and recorded workflow history, not a fresh local test; **Not configured** = provider execution is explicitly unavailable; **Not evidenced** = no source/test evidence sufficient to claim the live capability.

## Operation matrix

| Operation | Tool binding | Current behavior / evidence | Limit |
|---|---|---|---|
| `qa_test_plan` | `workforce_qa_test_plan` | W9 verifier records a tenant-scoped QA/DevOps artifact with provenance and `provider_execution=not_configured`. | Test-plan artifact only; no test runner is invoked by this semantic handler. |
| `regression_analysis` | `workforce_regression_analysis` | Registered to `execute_qa_devops`; persists supplied repository, commit, scope, finding, evidence, and recommendation fields. | No repository diff analysis or regression test execution is evidenced by this handler. |
| `ci_health_check` | `workforce_ci_health_check` | Registered semantic operation; persists an analysis artifact. | Does not query a CI provider or fetch current workflow status. |
| `release_readiness` | `workforce_release_readiness` | Registered semantic operation; persists an analysis artifact. | No live release-gate aggregation or repository-specific evidence collection is performed here. |
| `incident_diagnostics` | `workforce_incident_diagnostics` | Registered semantic operation; persists supplied incident/evidence fields. | No monitoring, logs, alert, or incident-management provider is connected by this handler. |
| `rollback_readiness` | `workforce_rollback_readiness` | Registered semantic operation; persists an analysis artifact. | Readiness analysis only; it does not roll back a deployment or verify a target environment. |
| `deployment_proposal` | `workforce_deployment_proposal` | Approval-gated proposal; W9 verifier confirms proposal state and fail-closed provider status. | No deployment adapter or completed deployment is evidenced. |
| `rollback_proposal` | `workforce_qa_rollback_proposal` | The role contract maps this operation to a dedicated QA rollback proposal tool. It is approval-gated and routed to `execute_qa_devops`. | Proposal only; no rollback provider execution or post-rollback health verification is evidenced. |
| `production_change_proposal` | `workforce_production_change_proposal` | Approval-gated proposal persisted through the semantic handler. | No production mutation adapter or completed change is evidenced. |

## Governance and evidence boundary

- The role contract classifies the six analysis/readiness operations as routine and the deployment, rollback, and production-change proposals as approval-required.
- Registry handlers route these operations to `execute_qa_devops`, which explicitly sets `provider_execution=not_configured`, persists a tenant-scoped `qa_devops_artifact`, and does not execute deployment.
- Existing W9 certification covers the governed research Run, artifact provenance, cross-tenant artifact-read denial, an approval-bound deployment proposal, and provider fail-closed status. This is source/repository CI evidence; it does not establish live CI, deployment, monitoring, or rollback integration.
- The repository's other CI workflows can validate code and run project tests. That is separate from the QA & DevOps employee's own `ci_health_check` tool, which currently does not query those workflows at runtime.
- No fresh local pytest, live CI-provider query through this role, deployment, rollback, production change, incident-provider request, or post-change health check was performed for this checkpoint.

## Requirements before claiming live QA/DevOps capability

Before binding external providers, define and test:
- tenant/repository authorization and exact repository/commit identity for every read;
- CI run identity, branch/commit association, freshness, pagination, and failure/unknown-state behavior;
- test execution boundaries, command allowlists, resource limits, and artifact capture for regression analysis;
- provenance and severity rules for incident inputs, including source timestamps and missing-data behavior;
- approval-bound idempotent deployment/rollback adapters, preconditions, immutable target identity, and execution receipts;
- explicit outcome states separating proposal, provider acceptance, completed deployment/rollback, and independently verified health;
- tenant-isolation, unauthorized-repository, stale-result, provider-timeout, retry, and approval replay/mismatch tests.

**Progress remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
