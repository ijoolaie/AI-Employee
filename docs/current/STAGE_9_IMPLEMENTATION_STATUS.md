# Stage 9 — Autonomous Workforce Optimization

## Current status

**Status: CURRENT PLANNED SLICES IMPLEMENTED; PRESENT IN CURRENT RELEASE v1.4.7**

Stage 9 builds on the governed execution substrate completed and evidenced through Stage 8. The implemented slices add deterministic optimization primitives and bounded lifecycle/control behavior without allowing an optimizer to bypass lifecycle, authorization, approval, concurrency, budget, audit or execution controls.

The planned Stage 9 slices were implemented and exact-SHA certified as part of release `v1.4.2`, and remain included in current release `v1.4.7`.

## Implemented slices

### 1. Capability-aware routing

`backend/app/services/agent_optimization.py` provides `select_agent()` and requires requested capabilities, available capacity and policy-compliant risk tier. Tie-breaking is deterministic using fitness, remaining capacity, capability coverage and stable Agent instance ID.

### 2. Task/risk/cost-aware model selection

`select_model()` filters provider/model candidates by task risk and maximum cost policy, then applies task cost/latency weights with deterministic tie-breaking. This is recommendation-only and does not change provider configuration, budgets, lifecycle, permissions or approval policy.

### 3. Queue-aware workload balancing

`backend/app/services/workload_balancing.py` calculates normalized queue pressure from ready depth, available capacity and oldest-ready age; filters unavailable Agents; selects a deterministic target; fails closed without eligible capacity; and emits an explicit recommendation and rationale. It does not mutate WorkItems or Agent state.

### 4. Persisted workload-balancing evidence

`backend/app/models/workload_balance_event.py` and migration `p810workloadbalance` persist tenant-scoped queue/load recommendation evidence. `GET /api/v1/admin/workload-balance/history` exposes read-only history through the existing admin boundary. No assignment or Agent mutation is introduced.

### 5. Telemetry-backed Agent fitness

`backend/app/services/agent_fitness.py` derives bounded tenant-scoped fitness from durable Run, AIProviderCall and Feedback records. Missing feedback is missing evidence, not a zero score. `GET /api/v1/admin/agent-fitness` is read-only.

### 6. Agent version fitness

`backend/app/services/agent_version_fitness.py` aggregates the bounded fitness contract by tenant-scoped AgentTemplate version. `GET /api/v1/admin/agent-version-fitness` exposes identity, sample counts, component scores, composite fitness, window and contract version. It does not mutate lifecycle state.

### 7. Promotion evidence

`backend/app/services/agent_promotion_evidence.py` builds a neutral candidate-vs-nearest-prior comparison with sample counts, fitness values/delta, comparability, evidence window and contract version. `GET /api/v1/admin/agent-promotion-evidence` is evidence-only.

### 8. Governed promotion

`backend/app/services/agent_promotion.py` requires comparable evidence, eligible draft/evaluating state, existing Stage 8 evaluation/policy evidence, and independently attributable requester/approver. `POST /api/v1/agent-templates/{template_id}/promote` reuses the existing `publish_template()` governance path and audit service.

### 9. Governed rollback planning

`backend/app/services/agent_rollback.py` deterministically selects the immediately prior published version of the same template slug/definition and creates a normal workforce replacement proposal. `POST /api/v1/agent-workforce/replacements/rollback` requires independent requester/sponsor. Existing prepare-cutover/cutover remains the only execution path.

### 10. Workforce capacity forecasting

`backend/app/services/capacity_forecasting.py` provides a read-only bounded forecast from WorkItem arrivals, completed Agent Run duration telemetry, current READY/active workload and enabled max concurrency. `GET /api/v1/admin/capacity-forecast` exposes projected arrivals, required concurrency, utilization, backlog, sensitivity bounds, evidence completeness and contract version. Missing service-time telemetry fails closed.

### 11. Governed workforce scaling control loop

`backend/app/services/governed_scaling.py` converts complete forecast evidence into a bounded workforce scaling proposal only when projected demand exceeds available capacity. It requires a real published AgentTemplate, binds risk tier to that template, caps additional concurrency, requires independent requester/sponsor, and reuses the existing governed workforce proposal path.

Provisioning, access review, activation, concurrency, audit and execution remain behind existing governance. The optimizer never directly creates an AgentInstance, enables it, assigns WorkItems or grants execution authority.

## Acceptance and release evidence

Stage 9 service tests cover routing/model selection, workload balancing and persisted evidence, telemetry fitness, version fitness, promotion evidence, governed promotion, rollback, capacity forecasting and governed scaling invariants.

The Stage 9 implementation was included in the certified v1.4.2 release and remains present in v1.4.7. The current v1.4.7 Production Certification run `35498984521` passed with 0 Product Gate Failures.

## Explicitly not claimed

Stage 9 release certification does **not** claim external production deployment, live provider acceptance, measured production SLO/SLI or error budget, real backup/restore/DR RPO/RTO, deployed-target DAST, independent penetration testing, or final Vendor/Reseller/Client external acceptance.

These remain external production-boundary items and are tracked separately.

## Exit direction

The current planned Stage 9 implementation is release-certified and present in v1.4.7. Future Stage 9 work should be driven by measured optimizer evidence and concrete product requirements, not by reimplementing Stage 8 governance. Any future code change must receive fresh exact-SHA CI/certification before release promotion.

Human governance remains above optimization. Optimization recommendations and control loops cannot authorize an action that the Stage 8 policy kernel would deny.
