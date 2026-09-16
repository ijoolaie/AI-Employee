# Stage 9 — Autonomous Workforce Optimization

## Current status

**Status: ACTIVE — optimization foundation implemented**

Stage 9 begins from the governed execution substrate completed and evidenced in Stage 8. This slice deliberately adds a deterministic optimization kernel rather than allowing an optimizer to bypass lifecycle, authorization, approval, concurrency, or budget controls.

## Implemented in this slice

### 1. Capability-aware routing

`backend/app/services/agent_optimization.py` provides `select_agent()` and requires:

- requested capabilities to be present on the candidate;
- candidate capacity to be available;
- candidate risk tier to satisfy both task and tenant/application policy bounds.

Tie-breaking is deterministic using fitness, remaining capacity, capability coverage, and stable Agent instance ID.

### 2. Task/risk/cost-aware model selection

`select_model()` filters provider/model candidates by task risk and an explicit maximum cost policy, then applies task cost/latency weights with deterministic tie-breaking.

This is a recommendation boundary. It does not change provider configuration, budgets, Agent lifecycle, permissions, or approval policy.

### 3. Fail-closed behavior

No eligible Agent returns no decision. If a model is required and no model satisfies the policy, optimization also returns no decision. Existing execution services remain the authority for authorization and side effects.

### 4. Acceptance evidence

`backend/tests/services/test_agent_optimization.py` covers capability/capacity/risk filtering, deterministic tie-breaking, model cost/risk bounds, contract metadata, and fail-closed behavior.

## Explicitly not claimed yet

The following remain subsequent Stage 9 increments:

- persisted workload-balancing state and queue-aware rebalancing;
- production telemetry-backed fitness computation;
- Agent version fitness, promotion, and rollback workflow;
- workforce capacity forecasting;
- autonomous scaling/rebalancing execution behind governance controls;
- provider-specific model catalog/latency/cost telemetry integration;
- production certification of any promoted code.

Human governance remains above optimization. Optimization recommendations cannot authorize an action that the Stage 8 policy kernel would deny.

## Exit direction

Stage 9 should grow these primitives through measurable evidence and bounded control loops. It should not duplicate the Stage 8 policy, identity, approval, budget, audit, or execution mechanisms.
