# Stage 9 — Autonomous Workforce Optimization

## Current status

**Status: ACTIVE — optimization foundation, queue-aware balancing, persisted balancing evidence, and telemetry-backed fitness implemented**

Stage 9 builds on the governed execution substrate completed and evidenced in Stage 8. The implemented slices add deterministic optimization primitives without allowing an optimizer to bypass lifecycle, authorization, approval, concurrency, or budget controls.

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

### 6. Acceptance evidence

`backend/tests/services/test_agent_optimization.py` covers capability/capacity/risk filtering, deterministic tie-breaking, model cost/risk bounds, contract metadata, and fail-closed behavior.

`backend/tests/services/test_workload_balancing.py` covers queue-pressure calculation, threshold suppression, deterministic capacity selection, disabled-Agent filtering, persisted snapshot creation, and bounded history queries.

`backend/tests/services/test_agent_fitness.py` covers bounded composite scoring, feedback handling, and empty-sample fail-closed behavior.

## Explicitly not claimed yet

The following remain subsequent Stage 9 increments:

- Agent version fitness, promotion, and rollback workflow;
- workforce capacity forecasting;
- autonomous scaling/rebalancing execution behind governance controls;
- provider-specific model catalog/telemetry integration beyond the existing provider-call records;
- production certification of any promoted code.

Human governance remains above optimization. Optimization recommendations cannot authorize an action that the Stage 8 policy kernel would deny.

## Exit direction

Stage 9 should grow these primitives through measurable evidence and bounded control loops. It should not duplicate the Stage 8 policy, identity, approval, budget, audit, or execution mechanisms.
