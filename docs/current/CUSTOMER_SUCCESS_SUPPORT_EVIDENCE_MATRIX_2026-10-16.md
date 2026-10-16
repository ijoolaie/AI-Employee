# Customer Success & Support Evidence Matrix — 2026-10-16

## Scope and evidence rules

This checkpoint maps the `ai_customer_success` role contract to registered tools, its semantic handler, and existing repository evidence. A customer-support artifact is not proof that a CRM, ticket system, inbox, or messaging provider was queried. A proposal marked as an external action is not proof that a message, refund, account change, or cancellation occurred.

Evidence labels: **Artifact-backed** = a tenant-scoped artifact/result is persisted; **CI/source evidence** = repository implementation and recorded CI workflow history, not a fresh local test; **Not configured** = provider execution is explicitly unavailable; **Not evidenced** = no source/test evidence sufficient to claim the live capability.

## Operation matrix

| Operation | Tool binding | Current behavior / evidence | Limit |
|---|---|---|---|
| `customer_context` | `workforce_customer_context` | W8 verifier and the deterministic Workforce Semantic Real-Stack lifecycle document a successful Run and tenant-scoped `customer_success_artifact`, with provenance and `provider_execution=not_configured`. | Request/analysis artifact only; no live CRM, account, or support-history retrieval is established. |
| `support_triage` | `workforce_support_triage` | Registered to `execute_customer_success`; existing semantic verifier records a tenant-scoped analysis artifact. | Triage is not proven to have read a live ticket queue or customer conversation. |
| `conversation_summary` | `workforce_conversation_summary` | Registered handler persists the supplied query/evidence/message fields as a tenant-scoped artifact. | No source conversation ingestion or provider-backed summary quality evaluation is evidenced. |
| `churn_risk_evidence` | `workforce_churn_risk_evidence` | Registered handler persists supplied evidence and recommendation fields. | No measured churn model, historical outcome validation, or customer-data connector is evidenced. |
| `escalation_recommendation` | `workforce_escalation_recommendation` | Registered handler persists analysis/recommendation state. | Recommendation artifact only; no live ticket escalation or SLA system action. |
| `response_draft` | `workforce_response_draft` | Registered handler persists a response-related analysis artifact. | No external delivery; no proof that the draft is fact-checked against a live customer record. |
| `customer_health_report` | `workforce_customer_health_report` | Registered handler persists a tenant-scoped report artifact. | No connected product-usage, billing, ticket, or CRM signals are evidenced; report inputs must not be described as independently verified. |
| `send_customer_message` | `workforce_send_customer_message` | Registry marks it as an external side-effect tool requiring approval. W8 certification verifies an approved tool-call path produces a pending proposal with `provider_execution=not_configured`. | Approval does not send the message. No live messaging provider or delivery receipt is established. |
| `account_change_proposal` | `workforce_account_change_proposal` | Approval-gated proposal binding. | Proposal only; no account mutation adapter or completed change evidenced. |
| `refund_proposal` | `workforce_refund_proposal` | Approval-gated proposal binding. | Proposal only; no refund execution or payment-provider receipt evidenced. |
| `cancellation_proposal` | `workforce_cancellation_proposal` | Approval-gated proposal binding. | Proposal only; no cancellation execution or provider confirmation evidenced. |

## Governance and evidence boundary

- The role contract classifies the seven analysis/report operations as routine and the four customer-facing or account-impacting operations as approval-required.
- The registry applies `requires_approval=True` and external-side-effect flags to `send_customer_message` and the three `*_proposal` operations. The semantic handler still returns `provider_execution=not_configured`; those flags describe the governed boundary, not a completed external side effect.
- Existing W8 certification covers the customer-context path, a customer-message proposal, approval governance, tenant provenance, cross-tenant artifact-read denial, and fail-closed provider status. The repository also records a deterministic WorkItem → assignment → dispatch → worker → successful Run lifecycle for `workforce_customer_context`.
- These checks are repository/CI evidence. No fresh local pytest, live CRM/support-platform read, outbound message, refund, account mutation, cancellation, or delivery receipt was performed for this checkpoint.

## Requirements before claiming live customer success

Before connecting a real support/CRM provider, define and test:
- tenant-scoped source records and authorization for customer identity, conversation, ticket, account, and billing data;
- provenance, source IDs, freshness, pagination, deduplication, and missing/conflicting data behavior;
- evidence-backed triage and churn-risk rules, including calibrated thresholds and an explanation of unknown signals;
- idempotent, approval-bound external actions with provider receipts and safe retry behavior;
- tenant-isolation, permission-denial, approval mismatch/replay, and provider failure tests;
- separate completion states for proposal created, provider request accepted, and externally confirmed outcome.

**Progress remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
