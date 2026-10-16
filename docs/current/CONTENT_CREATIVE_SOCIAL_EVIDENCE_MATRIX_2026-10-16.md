# Content, Creative, and Social Workforce Evidence Matrix — 2026-10-16

## Scope and evidence rules
This checkpoint maps AI Content Producer, AI Graphic Designer, and AI Social Media Employee role contracts to registry bindings, semantic dispatch, persistence, approval controls, and existing tests. A saved proposal is not a completed external action.

Evidence labels: **Artifact-backed** = tenant-scoped record persisted; **Deterministic check** = structural rule only; **Approval-gated proposal** = external action requested but not executed; **Not configured** = provider unavailable/fail-closed; **CI/source evidence** = code/test history, not fresh local test or live provider validation.

## AI Content Producer

| Operation | Binding | Implementation / result | Evidence and limit |
|---|---|---|---|
| `produce_article` | `workforce_produce_article` | Persists versioned content draft | W3 tests cover unique IDs and tenant-scoped storage; no CMS publishing. |
| `produce_social_caption` | `workforce_produce_social_caption` | Persists versioned content draft | W3 tests include tenant separation; no social posting. |
| `produce_short_form` | `workforce_produce_short_form` | Persists versioned content draft | No independent media-generation provider implied. |
| `prepare_cta` | `workforce_prepare_cta` | Persists content draft | Artifact preparation only. |
| `prepare_content_calendar` | `workforce_prepare_content_calendar` | Persists content draft | No scheduler execution implied. |
| `prepare_content_brief` | `workforce_prepare_content_brief` | Persists content draft | Brief artifact only. |
| `repurpose_content` | `workforce_repurpose_content` | Persists content draft | No external publishing integration evidenced. |
| `content_qa` | `workforce_content_qa` | Deterministic title/body presence and placeholder-marker checks; saves report | Tests cover pass/fail and tenant-scoped readback. Does not assess factual accuracy, tone, brand, or legal compliance. |
| `external_content_commitment` | **None** | Approval-required and unbound | External commitment unavailable through this role contract. |

## AI Graphic Designer

| Operation | Binding | Implementation / result | Evidence and limit |
|---|---|---|---|
| `create_visual_asset` | `workforce_create_visual_asset` | Persists creative request draft | Tests cover unique IDs, tenant scope, and `provider_execution=not_configured`; no generated image claimed. |
| `revise_visual_asset` | `workforce_revise_visual_asset` | Persists creative request draft | No image-edit provider execution evidenced. |
| `prepare_brand_variant` | `workforce_prepare_brand_variant` | Persists creative request draft | No asset render or license purchase. |
| `prepare_campaign_creative` | `workforce_prepare_campaign_creative` | Persists creative request draft | No campaign deployment or media provider execution. |
| `paid_asset_procurement` | **None** | Approval-required and unbound | No purchasing capability registered. |
| `commercial_license_purchase` | **None** | Approval-required and unbound | No license-purchasing capability registered. |
| `material_external_spend` | **None** | Approval-required and unbound | No spend capability registered. |
| `contractual_commitment` | **None** | Approval-required and unbound | No contract-execution capability registered. |

## AI Social Media Employee

| Operation | Binding | Implementation / result | Evidence and limit |
|---|---|---|---|
| `read_comments` | `workforce_read_comments` | Persists social operation request | Does not fetch live platform comments. |
| `triage_comments` | `workforce_triage_comments` | Persists social operation request | No external comment triage performed. |
| `read_analytics` | `workforce_read_analytics` | Persists social operation request | No external analytics query evidenced. |
| `publication_status` | `workforce_publication_status` | Persists social operation request | No platform status lookup performed. |
| `connect_channel` | `workforce_connect_channel` | Approval-gated proposal; provider `not_configured` | Side-effecting and approval-required; no OAuth/account link claimed. |
| `publish_post` | `workforce_publish_post` | Approval-gated proposal; provider `not_configured` | Tests cover approval state, persistence, tenant scope, dispatch mapping; no post published. |
| `publish_reel` | `workforce_publish_reel` | Approval-gated proposal; provider `not_configured` | No reel provider execution. |
| `publish_story` | `workforce_publish_story` | Approval-gated proposal; provider `not_configured` | No story published. |
| `schedule_publication` | `workforce_schedule_publication` | Approval-gated proposal; provider `not_configured` | No external schedule created. |
| `respond_to_dm` | `workforce_respond_to_dm` | Approval-gated proposal; provider `not_configured` | No customer message sent. |

## Cross-cutting findings

1. Role contracts, tool names, and semantic dispatch exist, but declarations do not prove a connected provider or an external result.
2. `backend/tests/test_workforce_w2_w6_semantic_domains.py` contains focused tests for content artifacts, deterministic QA, creative requests, social approval gating, tenant-scoped persistence, registry approval metadata, and operation-to-dispatch mapping.
3. Social publication and channel connection are marked side-effecting and approval-required. The current handler records proposals and explicitly reports `provider_execution=not_configured`; it does not execute against Instagram or another social platform.
4. Graphic design operations record requests and explicitly report `provider_execution=not_configured`; no actual image/video generation is claimed by these code paths.
5. Content QA is a limited deterministic structural check, not an AI quality judge.
6. Evidence is source inspection and repository CI/test history. No fresh local pytest, OAuth connection, live Meta/Instagram request, social post, or image-generation-provider run was performed.

## Next steps

- Keep these roles at proposal/artifact status until tenant-owned provider configuration, approval-resume validation, and supervised integration tests establish real execution.
- Before implementing providers, require positive and negative tests, tenant isolation, approval enforcement, idempotency/reconciliation for ambiguous writes, and an explicit execution receipt.
- Continue to another role after this checkpoint passes CI; change runtime behavior only for a concrete failing test or reproduced mismatch.

**Progress remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
