# Stage 9 — Autonomous Workforce Optimization

## Current status

**Status: ACTIVE — optimization foundation, queue-aware balancing, persisted balancing evidence, telemetry-backed fitness, Agent version fitness, promotion evidence, and governed promotion implemented**

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

The signal contains:

- success rate;
- optional normalized feedback score;
- latency score derived from provider-call latency;
- cost score derived from recorded Run cost;
- an explainable composite fitness value and explicit contract version.

`GET /api/v1/admin/agent-fitness` exposes the read-only signal to the existing platform-admin boundary. The service does not mutate Agent, Run, budget, approval, policy, or lifecycle state. Missing feedback is treated as missing evidence rather than a zero rating.

### 6. Agent version fitness

`backend/app/services/agent_version_fitness.py` aggregates the same bounded telemetry scoring contract by tenant-scoped `AgentTemplate` version through the existing `AgentInstance -> AgentTemplate` binding.

`GET /api/v1/admin/agent-version-fitness` exposes the read-only version-level signal, including template identity/version, participating instance count, sample count, component scores, composite fitness, time window, and contract version.

The version fitness slice is measurement only. It does not promote, demote, retire, mutate, assign, or change any AgentTemplate/AgentInstance state, and it does not bypass policy, approval, budget, identity, or lifecycle controls.

### 7. Promotion evidence

`backend/app/services/agent_promotion_evidence.py` builds a neutral candidate-vs-nearest-prior-version comparison using the same tenant-scoped fitness contract. Evidence includes candidate/baseline identity, sample counts, fitness values, fitness delta, comparability, evidence window, and contract version.

`GET /api/v1/admin/agent-promotion-evidence` exposes the evidence behind the existing platform-admin governance boundary.

This increment is evidence-only. It does not publish, promote, demote, retire, assign, mutate, or authorize lifecycle changes. Comparability is deliberately explicit when there is no measured prior version.

### 8. Governed promotion

`backend/app/services/agent_promotion.py` adds the first bounded Stage 9 lifecycle control. A candidate can only be promoted when:

- candidate-vs-prior-version evidence is available and comparable;
- the candidate is in an eligible draft/evaluating lifecycle state;
- the existing Stage 8 evaluation/policy evidence gate passes;
- requester and approver are independently attributable.

`POST /api/v1/agent-templates/{template_id}/promote` records the governed promotion through the existing audit service and reuses the existing `publish_template()` governance path rather than creating a parallel authorization mechanism. The optimization signal never grants authority by itself.

### 9. Acceptance evidence

`backend/tests/services/test_agent_optimization.py` covers capability/capacity/risk filtering, deterministic tie-breaking, model cost/risk bounds, contract metadata, and fail-closed behavior.

`backend/tests/services/test_workload_balancing.py` covers queue-pressure calculation, threshold suppression, deterministic capacity selection, disabled-Agent filtering, persisted snapshot creation, and bounded history queries.

`backend/tests/services/test_agent_fitness.py` covers bounded composite scoring, feedback handling, and empty-sample fail-closed behavior.

`backend/tests/services/test_agent_version_fitness.py` covers reuse of the bounded scoring contract, window bounds, and read-only contract semantics.

`backend/tests/services/test_agent_promotion_evidence.py` covers nearest-prior comparison, missing-baseline comparability, window bounds, and absence of lifecycle commands.

`backend/tests/services/test_agent_promotion.py` covers independent attribution, missing evidence fail-closed behavior, and reuse of the governed evaluation/publish path.

## Explicitly not claimed yet

The following remain subsequent Stage 9 increments:

- governed rollback workflow;
- workforce capacity forecasting;
- autonomous scaling/rebalancing execution behind governance controls;
- provider-specific model catalog/telemetry integration beyond the existing provider-call records;
- production certification of any promoted code.

Human governance remains above optimization. Optimization recommendations cannot authorize an action that the Stage 8 policy kernel would deny.

## Exit direction

Stage 9 should grow these primitives through measurable evidence and bounded control loops. It should not duplicate the Stage 8 policy, identity, approval, budget, audit, or execution mechanisms.
