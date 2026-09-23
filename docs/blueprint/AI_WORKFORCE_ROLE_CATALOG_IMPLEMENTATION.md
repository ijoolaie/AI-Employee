# AI Workforce Role Catalog — Initial Implementation Slice

## Status

**Post-v1.4.11 engineering — implemented catalog foundation; role instances are not claimed active.**

The certified `v1.4.11` release remains immutable. This document describes a new post-certification engineering boundary and does not change the certified release identity.

## Implemented in this slice

The backend now contains a declarative first-party workforce catalog for:

1. AI Internal Manager
2. AI Marketing & Advertising Manager
3. AI Graphic Designer
4. AI Software Developer
5. AI Trader

The catalog provides stable role codes, bilingual names, organizational category, reporting line, routine operations and explicitly approval-gated operations. The four specialized roles also have first-party workforce role templates exposed through the read-only catalog API.

## Workforce role templates

The first-party workforce template catalog currently contains:

1. AI Marketing & Advertising Manager
2. AI Graphic Designer
3. AI Software Developer
4. AI Trader

These are role templates, not active AgentTemplates or AgentInstances. The Internal Manager may select any catalog role for a proposal and may also propose a new role that is not yet in the catalog. A new role is human-approval-required by default and must go through AgentTemplate evaluation/publish before provisioning.

## Authority contract

### AI Internal Manager

The Internal Manager remains **CEO approval-by-default**.

The CEO may explicitly delegate bounded routine authority for task assignment, reprioritization, handoffs, workload balancing, workforce-capacity requests, management reporting, budget estimates and cost-optimization proposals.

Delegation does not authorize financial commitments, material resource commitments, security-sensitive changes, legal/contractual commitments, production-critical changes, irreversible actions, or high-impact hiring, retirement, transfer or replacement.

### Specialized workforce

All four specialized roles remain under Internal Manager supervision.

- Marketing & Advertising Manager: routine planning/analysis can be delegated; paid campaigns and material spend require human approval.
- Graphic Designer: routine creative production can be delegated; paid procurement/licensing requires approval.
- Software Developer: routine fixes/tests/refactors can be delegated; production-critical/security-sensitive changes remain approval-gated.
- Trader: research, risk analysis, trading plans and order staging can be prepared; capital allocation and actual financial execution require CEO/authorized-human approval.

## Provisioning boundary

This slice intentionally does **not** create active AgentInstances.

Actual provisioning continues through the governed path:

`AgentDefinition → AgentTemplate → evaluation/publish → workforce proposal → Board/CEO approval → AgentInstance → access review → activation`

This prevents a role catalog from being mistaken for a deployed workforce.

## Next implementation slice

The next application-code slice should connect the AI Internal Manager to the existing governed workforce proposal path, with:
- attributable Manager identity;
- manager-originated staffing/replacement proposals;
- durable CEO delegation records;
- explicit delegation scope, duration, affected employees, resource/spend limit, risk tier and revocation;
- audit events for delegation creation/revocation and manager actions;
- manager workload/KPI/SLA and capacity reporting;
- role-specific tools for Marketing, Graphic Design, Software Development and Trader;
- approval gates for high-impact operations.