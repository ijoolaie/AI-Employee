# Marketing Manager Evidence Matrix — 2026-10-16

## Scope and evidence rules

This checkpoint maps the `ai_marketing_advertising_manager` role contract to its registered tools, semantic handlers, and documented evidence. A campaign plan or sales-growth report is not proof of campaign-attributed performance. A persisted proposal is not an external action.

Evidence labels: **Artifact-backed** = a tenant-scoped artifact/result is persisted; **CI/source evidence** = repository implementation and test/workflow history, not a fresh local test; **Unbound** = no approved Tool Registry binding; **Not evidenced** = no source/test evidence sufficient to claim the capability.

## Operation matrix

| Operation | Tool binding | Current behavior / evidence | Limit |
|---|---|---|---|
| `draft_campaign_plan` | `workforce_draft_campaign_plan` | Deterministic structured plan with objective, audience, channels, duration, optional budget/offer, phases, metrics, and governance fields. | Planning draft only; does not launch campaigns, spend, contact platforms, or measure outcomes. The service explicitly says attribution requires measured data. |
| `coordinate_content` | `workforce_coordinate_content` | Tenant-scoped, channel-aware content work package. | Coordination artifact only; no publication, external provider access, campaign launch, spend, or attribution implied. |
| `prepare_growth_report` | `workforce_prepare_growth_report` | Read-only report over tenant-owned orders and sales-deal data. PR #1124 recorded deterministic real-stack WorkItem → assignment → dispatch → worker → successful Run evidence. | Commercial growth summary only; does not establish ad-platform analytics or campaign attribution. Evidence is CI/fixture-backed, not a live marketing-provider run. |
| `analyze_campaign_performance` | **None** | Explicitly remains unbound; regression coverage was added in PR #1092. | Must fail closed until a campaign-specific measured-data domain, reviewed handler/binding, and tests exist. Do not substitute `prepare_growth_report`. |
| `paid_campaign_launch` | **None** | Approval-required; no registered execution binding. | No live campaign launch capability established. |
| `material_ad_spend` | **None** | Approval-required; no registered execution binding. | No spend capability established. |
| `contractual_commitment` | **None** | Approval-required; no registered execution binding. | No contract execution established. |
| `external_purchase` | **None** | Approval-required; no registered execution binding. | No purchasing capability established. |

## Important separation of concepts

1. **Campaign planning** answers what should be tried; its metrics are proposed success measures, not observed results.
2. **Commercial growth reporting** summarizes tenant-owned order/deal records. It cannot infer which campaign caused an order without explicit measured attribution data.
3. **Campaign performance analysis** requires campaign identifiers, observed spend/impressions/clicks/conversions (or other clearly defined source metrics), timestamps, source provenance, tenant isolation, and a documented attribution rule. The current role has no proven dedicated domain/binding for this operation.
4. **Execution** (launching campaigns, spending money, purchases, or contractual commitments) remains unbound. Human-approval classification alone does not implement an execution adapter.

## Next implementation gate for campaign attribution

Do not bind `analyze_campaign_performance` to a generic report. Before implementing it, define and test:
- a tenant-owned campaign/event data model and supported ingestion source(s);
- explicit metric definitions, currency/time-window normalization, missing-data behavior, and attribution method;
- provenance and freshness for every reported metric, with no inferred causality when campaign linkage is absent;
- tenant-isolation and authorization negative tests;
- deterministic fixture coverage for valid, empty, partial, conflicting, and cross-tenant data;
- a persisted report/receipt that records data window, source, attribution rule, and limitations;
- a read-only execution boundary unless a separately reviewed approval-gated campaign execution adapter is implemented.

## Evidence boundary

This matrix is based on source inspection and repository CI/test history, including the existing negative binding regression for `analyze_campaign_performance` and the documented PR #1124 growth-report lifecycle. No fresh local pytest, live ad-platform API request, campaign launch, paid spend, or live attribution calculation was performed.

**Progress remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
