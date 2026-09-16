# Stage 9 — Autonomous Workforce Optimization

## Current status

**Status: ACTIVE — optimization foundation, queue-aware balancing, persisted balancing evidence, telemetry-backed fitness, Agent version fitness, promotion evidence, governed promotion, governed rollback planning, capacity forecasting, and governed workforce scaling implemented**

Stage 9 builds on the governed execution substrate completed and evidenced in Stage 8. The implemented slices add deterministic optimization primitives and bounded lifecycle control without allowing an optimizer to bypass lifecycle, authorization, approval, concurrency, or budget controls.

## Implemented slices

### 1. Capability-aware routing

`backend/app/services/agent_optimization.py` provides `select_agent()` and requires:

- requested capabilities to be present on the candidate;
- candidate capacity to be available;
- candidate risk tier to satisfy both task and tenant/application policy bounds.

Tie-breaking is deterministic using fitness, remaining capacity, capability coverage, and stable Agent instance ID.

### 2. Task/risk/cost-aware model selection

`select_model()` filters provider/model candidates by task risk and an explicit maximum cost policy, then applies task cost/latency weights with deterministic tie-breaking.

This is a recommendation boundary. It does not change provider configuration, budgets, Agent lifecycle, permissions, or approval policy.

### 3. Queue-aware workload balancing

`backend/app/services/workload_balancing.py` adds a deterministic recommendation layer that:

- calculates normalized queue pressure from ready-item depth, available capacity, and oldest-ready age;
- filters out Agents that are not accepting work or have no available slots;
- selects a target deterministically using available slots, active load, and stable Agent instance ID;
- fails closed when no eligible capacity exists;
- emits an explicit recommendation-only contract and rationale.

The recommendation consumes authoritative queue/load snapshots but does not mutate WorkItems or Agent state.

### 4. Persisted workload-balancing evidence

`backend/app/models/workload_balance_event.py` and migration `p810workloadbalance` persist tenant-scoped recommendation snapshots containing queue depth, oldest-ready age, available capacity, pressure, target Agent, rationale, candidate count, and contract version.

`backend/app/services/workload_balance_history.py` provides the persistence and tenant-scoped history query boundary. `GET /api/v1/admin/workload-balance/history` exposes read-only history behind the existing platform-admin governance boundary.

This increment persists recommendation evidence only. It does not assign WorkItems, mutate Agent state, bypass policy/approval/budget controls, or introduce an autonomous control loop.

### 5. Telemetry-backed Agent fitness

`backend/app/services/agent_fitness.py` derives a bounded fitness signal from durable tenant-scoped `Run`, `AIProviderCall`, and per-Run `Feedback` records already persisted by the platform.

The signal contains success rate, optional normalized feedback score, latency score, cost score, an explainable composite fitness value, and an explicit contract version.

`GET /api/v1/admin/agent-fitness` exposes the read-only signal to the existing platform-admin boundary. Missing feedback is treated as missing evidence rather than a zero rating.

### 6. Agent version fitness

`backend/app/services/agent_version_fitness.py` aggregates the same bounded telemetry scoring contract by tenant-scoped `AgentTemplate` version through the existing `AgentInstance -> AgentTemplate` binding.

`GET /api/v1/admin/agent-version-fitness` exposes the read-only version-level signal, including template identity/version, participating instance count, sample count, component scores, composite fitness, time window, and contract version.

The version fitness slice is measurement only. It does not promote, demote, retire, mutate, assign, or change any AgentTemplate/AgentInstance state.

### 7. Promotion evidence

`backend/app/services/agent_promotion_evidence.py` builds a neutral candidate-vs-nearest-prior-version comparison using the same tenant-scoped fitness contract. Evidence includes candidate/baseline identity, sample counts, fitness values, fitness delta, comparability, evidence window, and contract version.

`GET /api/v1/admin/agent-promotion-evidence` exposes the evidence behind the existing platform-admin governance boundary.

This increment is evidence-only. It does not authorize lifecycle changes.

### 8. Governed promotion

`backend/app/services/agent_promotion.py` adds the first bounded Stage 9 lifecycle control. A candidate can only be promoted when candidate-vs-prior evidence is available and comparable, the candidate is in an eligible draft/evaluating state, the existing Stage 8 evaluation/policy evidence gate passes, and requester/approver are independently attributable.

`POST /api/v1/agent-templates/{template_id}/promote` reuses the existing `publish_template()` governance path and audit service rather than creating a parallel authorization mechanism.

### 9. Governed rollback planning

`backend/app/services/agent_rollback.py` adds a governed rollback entry point for an existing AgentInstance. It deterministically selects the immediately prior **published** version of the same AgentTemplate slug and AgentDefinition, then creates a normal workforce replacement proposal targeting that version.

`POST /api/v1/agent-workforce/replacements/rollback` requires an independently attributable requester and sponsor. Proposal creation does not mutate the active AgentInstance or change execution authority. The existing replacement `prepare-cutover` and `cutover` path remains the only execution path.

### 10. Workforce capacity forecasting

`backend/app/services/capacity_forecasting.py` provides a read-only forecast over a bounded historical window and future horizon. It combines tenant-scoped WorkItem arrival volume, completed Agent Run duration telemetry, current READY/active workload, and enabled Agent max-concurrency capacity.

`GET /api/v1/admin/capacity-forecast` exposes projected arrivals, required concurrency, utilization, projected backlog, descriptive sensitivity bounds, evidence completeness, and the forecast contract version.

The forecast is evidence-only. Missing service-time telemetry is not imputed as zero, and forecast pressure cannot change `max_concurrency`, enable/disable Agents, provision workforce, or assign WorkItems.

### 11. Governed workforce scaling control loop

`backend/app/services/governed_scaling.py` converts complete capacity-forecast evidence into a bounded workforce scaling proposal when projected demand actually exceeds available capacity.

The control loop:

- fails closed on incomplete forecast evidence;
- requires a real tenant-scoped published AgentTemplate;
- binds the proposal risk tier to the selected template;
- caps requested additional concurrency;
- requires independently attributable requester and sponsor;
- creates the existing governed workforce proposal rather than provisioning or enabling an Agent directly.

Provisioning, access review, activation, concurrency, audit, and execution remain behind the existing workforce governance path. The optimizer never directly creates an AgentInstance, enables it, assigns WorkItems, or grants execution authority.

## Acceptance evidence

The Stage 9 service tests cover optimization routing/model selection, workload balancing and persisted evidence, telemetry-backed fitness, version fitness, promotion evidence, governed promotion, governed rollback, capacity forecasting, and governed scaling control-loop invariants.

The governed scaling acceptance tests specifically cover independent sponsor attribution, incomplete-evidence fail-closed behavior, reuse of the existing workforce proposal path, and rejection when projected capacity is not overloaded.

PR #528 was merged to `main` at commit `7275f6efbb4b3502b242586f506c93d8c431763e`. Its post-fix CI and security/architecture/runtime gates completed successfully before merge.

## Explicitly not claimed yet

The following remain subsequent Stage 9/release work:

- production certification of the promoted code through the release-grade certification workflow;
- provider-specific model catalog/telemetry integration beyond the existing provider-call records.

Human governance remains above optimization. Optimization recommendations and control loops cannot authorize an action that the Stage 8 policy kernel would deny.

## Exit direction

Stage 9 should grow these primitives through measurable evidence and bounded control loops. It should not duplicate the Stage 8 policy, identity, approval, budget, audit, or execution mechanisms.
