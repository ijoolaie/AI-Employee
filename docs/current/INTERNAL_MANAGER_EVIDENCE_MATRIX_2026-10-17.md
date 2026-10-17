# AI Internal Manager — Capability Evidence Matrix (2026-10-17)

## Purpose and evidence standard

This matrix distinguishes registered capability and tested lifecycle evidence from product-level claims. Source inspection is not a live execution test. A successful canonical real-stack test proves only the exercised operation and denial paths, not every operation in the role catalog.

## Role contract and registered tools

The `ai_internal_manager` role declares eight routine/delegable operations:

| Operation | Registered tool | What the source supports | Evidence status / limit |
|---|---|---|---|
| `assign_task` | `workforce_assign_task` | Requires an active tenant Run context and routes into `assign_work_item`. The registry marks it side-effecting but not approval-required. | Tool registration and code path confirmed. W1 real-stack evidence includes assignment/dispatch lifecycle; do not infer arbitrary task assignment scenarios are all tested. |
| `reprioritize_task` | `workforce_reprioritize_task` | Dedicated registry binding. | Binding exists; no live provider action implied. |
| `coordinate_handoff` | `workforce_coordinate_handoff` | Dedicated registry binding; registry passes the current agent instance into the handler. | Binding exists; cross-employee handoff is not generally proven by the CEO-report test alone. |
| `balance_workload` | `workforce_balance_workload` | Dedicated registry binding. | Binding exists; no proof of automatic optimization across every workload case. |
| `request_workforce_capacity` | `workforce_request_capacity` | Dedicated registry binding. | Binding exists; request does not equal hiring/provisioning or capacity creation. |
| `prepare_ceo_report` | `workforce_prepare_ceo_report` | Tenant-scoped executive/workforce report path. Dashboard evidence reads tenant-scoped AgentInstance, WorkItem and WorkforceSLAContract records; SLA is marked disabled/not_configured when no active tenant SLA contract exists. | Strongest role evidence: W1 canonical real-stack lifecycle passed for CEO report, including WorkItem → assignment → dispatch → worker → successful Run, audit identity, active runtime binding, bounded CEO delegation, and denial cases. Report is a point-in-time snapshot, not historical SLA analytics. |
| `prepare_budget_estimate` | `workforce_prepare_budget_estimate` | Dedicated registry binding. | Binding exists; estimate is not budget approval, financial commitment, or accounting evidence. |
| `prepare_cost_optimization` | `workforce_prepare_cost_optimization` | Dedicated registry binding. | Binding exists; recommendation is not proof of realized savings. |

Sources:
- [Role contracts](https://github.com/ijoolaie/AI-Employee/blob/main/backend/app/services/ai_workforce_roles.py)
- [Tool registry](https://github.com/ijoolaie/AI-Employee/blob/main/backend/app/ai/tool_registry.py)
- [Delegation service](https://github.com/ijoolaie/AI-Employee/blob/main/backend/app/services/workforce_delegation_service.py)
- [W1 real-stack verifier](https://github.com/ijoolaie/AI-Employee/blob/main/backend/scripts/e2e_workforce_w1_control_plane_verify.py)
- [Existing capability audit and W1 evidence](https://github.com/ijoolaie/AI-Employee/blob/main/docs/current/CAPABILITY_REALITY_AUDIT_AND_COMMERCIAL_READINESS_PLAN_2026-10-13.md)

## Delegation and governance boundary

The source implements durable, tenant-scoped CEO delegation rather than granting the Internal Manager blanket authority:

- The manager instance and its template must belong to the same tenant, the template capability contract must identify `ai_internal_manager`, and the instance must be enabled.
- Delegation requires timezone-aware start/expiry, expiry after start, a maximum duration of 365 days, risk tier 0–4, and a non-empty list of explicitly allowed operations from a fixed allowlist.
- The delegating/revoking user is checked against the tenant. Creation and revocation are audit-recorded.
- An operation must have a matching active, in-window delegation for that manager and tenant. When a delegation scopes affected employees, an out-of-scope employee is rejected.
- Revocation is tenant-scoped, locked for update, and cannot be repeated as if still active.
- Runtime governance invokes the delegation assertion for Internal Manager operations. Existing tests cover explicit delegation and runtime identity mismatch denial.

The allowed delegation operation vocabulary includes routine task coordination and proposal operations such as staffing, replacement, transfer, and retirement proposals. This is authority to prepare/submit a bounded proposal, not permission to execute a hire, transfer, retirement, irreversible action, or financial commitment.

## Approval-required operations

The role contract marks these operations as approval-required and does not bind them to routine execution tools in the role contract:

- `hire_or_provision_employee`
- `retire_employee`
- `transfer_employee`
- `replace_employee`
- `financial_commitment`
- `material_resource_commitment`
- `security_sensitive_change`
- `legal_commitment`
- `production_critical_change`
- `irreversible_action`

The existence of proposal-related services does not demonstrate execution of the consequential action. Any such execution must remain separately governed and explicitly verified.

## What is and is not demonstrated

**Demonstrated by repository evidence**
- Role contract and eight dedicated routine tool bindings.
- Tenant Run context enforcement on the assignment tool path.
- Durable CEO delegation with expiry, revocation, operation allowlist, tenant checks and audit events.
- CEO-report canonical real-stack workflow with successful Run lifecycle and negative authorization paths (documented by prior PR #1123 and its workflow evidence).

**Not demonstrated by this matrix**
- A live, autonomous CEO that correctly plans and dispatches every task across all employee roles.
- Exhaustive correctness of reprioritization, handoff, workload balancing, capacity requests, cost optimization or budget estimates in a fresh run.
- Automatic hiring, employee provisioning, transfers, retirement or replacement.
- Financial approvals/commitments, production changes, legal commitments, or irreversible operations.
- Historical SLA measurement, external provider integration, commercial customer acceptance, or revenue outcomes.

## Recommended next verification

Keep the next test narrowly bounded: exercise one routine operation other than `prepare_ceo_report` through the canonical Run/approval/delegation path (prefer `assign_task` or `coordinate_handoff`), and assert tenant provenance, audit identity, expected state transition, and cross-tenant/expired-or-revoked-delegation denial. Do not treat the existing CEO-report evidence as coverage for every manager operation.

## Change classification

Documentation-only evidence inventory. No runtime code changed and no fresh local pytest, real-stack workflow, or external provider action was run as part of this document.
