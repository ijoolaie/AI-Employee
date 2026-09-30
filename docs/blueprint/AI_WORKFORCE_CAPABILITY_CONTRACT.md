# Workforce Capability Contract

## Status

Post-v1.4.11 engineering. This slice does not change the certified release identity and does not claim external production execution.

## Contract

Each catalog operation now has a machine-readable contract:

- operation
- capability_code
- tool_names
- required_permissions
- approval_required

The contract is distinct from both the Role authorization decision and the Tool Registry permission decision.

## Execution boundary

The intended chain is:

Workforce Role → Operation → Capability → Tool Binding → Permission → Approval → Tenant/Access Controls → Execution

AgentExecutionAdapter.execute_tool() requires both:

1. the role/runtime governance decision; and
2. an explicit Role/Operation → Tool Registry binding.

An operation with no approved tool binding fails closed. The implementation deliberately does not infer a binding from the tool name.

## Current binding state

The first-party workforce operations currently have explicit capability contracts, but their tool_names are intentionally empty until a canonical Tool Registry tool has been reviewed and bound to that capability.

This prevents a generic existing tool from accidentally acquiring workforce authority merely because its name appears semantically related to an operation.

Therefore this slice is a capability-contract foundation, not a claim that every workforce operation is executable through the existing Tool Registry.

## Permission and approval separation

The capability contract declares the permissions/approval expectation, but it does not replace the existing Tool Registry checks.

The final execution path remains:

Role Governance → Tool Binding → Tool Permission → Tool Approval → Tenant/Access Review → Handler

A capability contract cannot grant a permission that the Tool Registry or Agent permission policy does not grant.

## Code-reconciled implementation status — 2026-09-30

- Internal Manager: concrete coordination/reporting/budget/cost bindings exist in the role catalog and Tool Registry path.
- Marketing Manager: concrete growth-report, campaign-plan and content-coordination bindings exist.
- Trader: concrete read-only market-research, risk-analysis and trading-plan bindings exist; these do not execute trades.
- Graphic Designer: role and operations exist, but no approved first-party creative/media execution binding currently exists.
- Software Developer: role and operations exist, but no approved first-party engineering-workspace/change-set execution binding currently exists.
- Instagram/social publishing: no governed first-party publish/comment/DM/analytics tool chain was verified in the code audit.
- Image/video generation: no dedicated governed first-party workforce generation tool chain was verified.

The authoritative executable boundary is code plus tests/evidence, not the role catalog or blueprint. See docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md for the phased implementation plan.

## Next slice

For each workforce role, review the actual Tool Registry and add only explicit, canonical bindings where the semantics, required permission, side effects, and approval policy are compatible.

Operations without a suitable canonical tool should receive a dedicated tool or remain non-executable at the tool boundary; they must not be auto-mapped to an approximate tool.

## AgentTemplate binding

For a catalog workforce role, an AgentTemplate must explicitly declare both `workforce_role_code` and the exact `workforce_capability_contract` snapshot. A Workforce Proposal cannot install a catalog role when its selected AgentTemplate is not bound to the same role contract. This prevents a proposal configuration from selecting a stronger or unrelated role than the published template was evaluated for.
