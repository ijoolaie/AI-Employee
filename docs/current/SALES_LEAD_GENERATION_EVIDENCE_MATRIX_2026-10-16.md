# Sales & Lead Generation Evidence Matrix — 2026-10-16

## Scope and evidence rules

This checkpoint maps the `ai_sales_lead_generation` role contract to Tool Registry bindings, semantic handlers, configured provider boundaries, and existing tests. A saved sales artifact is not proof of CRM research, enrichment, outreach delivery, or conversion attribution.

Evidence labels: **Artifact-backed** = tenant-scoped record persisted; **Deterministic heuristic** = explicit inputs are evaluated by fixed rules; **Queued** = an outbound action was accepted by the transactional outbox; **Not configured** = provider did not execute; **CI/source evidence** = source and repository test history, not a fresh local test or live CRM run.

## Operation matrix

| Operation | Binding | Current behavior / evidence | Limit |
|---|---|---|---|
| `lead_research` | `workforce_lead_research` | Persists a tenant-scoped sales-operation artifact. | No live web research, CRM lookup, or external lead source is evidenced by this semantic handler. |
| `lead_qualification` | `workforce_lead_qualification` | Scores five explicitly supplied Boolean signals, 20 points each; records passed and missing/unconfirmed signals. Existing tests cover 80-point qualification, zero-evidence outcome, persisted explanation, and tenant isolation. | Transparent heuristic only. It does not verify the truth of supplied signals or fetch CRM data. Missing means unconfirmed, not false. |
| `crm_enrichment` | `workforce_crm_enrichment` | Persists request/artifact. | No configured CRM adapter or external enrichment result is evidenced; provider status remains `not_configured`. |
| `prepare_outreach_draft` | `workforce_prepare_outreach_draft` | Persists draft/work request. | Does not send the message. |
| `prepare_follow_up_queue` | `workforce_prepare_follow_up_queue` | Persists follow-up work request. | No CRM task, calendar event, or external queue write evidenced. |
| `prepare_proposal` | `workforce_prepare_proposal` | Persists proposal artifact. | Proposal preparation is not contract acceptance or delivery to the customer. |
| `prepare_meeting_request` | `workforce_prepare_meeting_request` | Persists meeting-request artifact. | No calendar/meeting provider write evidenced. |
| `pipeline_reporting` | `workforce_pipeline_reporting` | Persists a sales-operation report artifact. | No source-backed CRM pipeline query is evidenced in this handler; do not treat it as a verified live pipeline report. |
| `conversion_attribution` | `workforce_conversion_attribution` | Persists a sales-operation artifact. | No event ingestion, conversion linkage, attribution method, or measured result is evidenced. This is not actual attribution analysis. |
| `external_outreach` | `workforce_external_outreach` | Approval-gated; uses an operator-configured SMTP provider and tenant Run context. When configured, validates recipients against the SMTP domain allowlist and queues `email.send` through the transactional outbox with a dedupe key. When unconfigured, fails closed without an external side effect. | A successful queue result proves enqueueing, not final delivery or customer response. No live SMTP delivery is claimed. |
| `contractual_commitment` | `workforce_contractual_commitment` | Approval-required; semantic artifact/proposal path. | No contract execution provider evidenced. |
| `material_commercial_action` | `workforce_material_commercial_action` | Approval-gated; requires a tenant Run DB context and a deal in proposal/negotiation stage with a positive amount, then calls the configured sales checkout provider using an idempotency key. | This is a payment/checkout-session boundary, not proof of completed payment or signed contract. Provider configuration and live execution were not verified in this audit. |

## Evidence and important distinctions

1. Existing W5 tests assert the nine routine sales operations persist tenant-scoped artifacts with `provider_execution=not_configured`, no external side effect, and cross-tenant read denial.
2. Lead qualification is a deterministic checklist score over user-supplied signals; it is not autonomous verification or a model confidence score.
3. The SMTP outreach adapter shares the existing SMTP recipient-domain allowlist and transactional outbox. A queue receipt must not be presented as delivery confirmation; delivery outcome needs separate outbox/worker evidence.
4. Conversion attribution is currently a named role operation and bound semantic tool, but no measured attribution engine is evidenced. Do not infer campaign/lead causality from sales notes or generic pipeline artifacts.
5. Routine artifacts, outbound outreach, and material commercial actions have different risk boundaries. Human approval is required for external outreach, contractual commitment, and material commercial action; approval metadata alone does not establish a configured provider or completed external action.

## Requirements before claiming real CRM or attribution capability

- Identify and configure a supported tenant-scoped CRM source, with credentials isolated from model-controlled arguments.
- Define lead identity/deduplication, provenance, freshness, field-level write policy, and cross-tenant negative tests before enabling enrichment.
- Define the conversion event, source/medium/campaign identifiers, reporting window, currency/time normalization, and attribution method before implementing `conversion_attribution`.
- Persist source references and data timestamps; report unknown/missing linkage explicitly rather than guessing.
- Test duplicate/retry behavior, provider timeouts, ambiguous writes, tenant isolation, and failure receipts.
- For outbound email, separately verify queue acceptance, worker delivery/failure, and retry/idempotency behavior. Never label `queued` as `delivered`.

## Evidence boundary

This matrix is based on source inspection and existing repository tests/CI history. No fresh local pytest, live CRM connection, external lead research, SMTP delivery, calendar write, payment, or real conversion-attribution calculation was performed.

**Progress remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
