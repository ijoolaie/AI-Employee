# Usage & Cost Reporting — As-Built v0.2.17

**Date:** 2026-08-07  
**Status:** Implemented / source-verified

## Purpose

v0.2.17 adds the first read-only Usage/Cost reporting surface. It does not introduce billing, invoicing, quota enforcement or new persistence tables. The existing `ai_provider_calls` table remains the source of truth for provider call usage, latency and recorded cost.

## Backend

New service:

`backend/app/services/usage_service.py`

New schema:

`backend/app/schemas/usage.py`

New API:

`GET /api/v1/usage/summary`

The endpoint is tenant-scoped through the authenticated Tenant Context and protected by the existing `audit.read` permission. Optional `from_at` and `to_at` query parameters constrain the report window.

## Reported metrics

- AI provider call count
- successful / failed call count
- prompt tokens
- completion tokens
- total tokens
- recorded USD cost
- average latency
- provider/model breakdown

## Cost semantics

The endpoint reports the cost value recorded by `AIGateway`. For local LM Studio, the provider accounting value remains `0.0 USD`. This is intentionally not presented as an invoice or charge to a customer.

## Frontend

New Customer Panel route:

`/usage`

The page displays summary metrics and provider/model breakdown and uses the existing authenticated API client. A Usage navigation item was added to the Customer sidebar.

## Security

- Tenant ID is derived from the authenticated token/context; clients cannot select another tenant.
- No raw model responses, API keys or provider secrets are exposed.
- The endpoint is reporting-only.

## Database / migrations

No migration is required. v0.2.17 reads existing `ai_provider_calls` rows only.

## Verification

- Backend source compilation: PASS.
- Usage response contract test: PASS.
- Frontend source updated; production build remains environment-dependent because release archives intentionally do not contain `node_modules`.

## Deliberate non-goals

The following remain separate future phases:

- tenant quotas and hard usage limits;
- invoice generation;
- payment collection;
- billing plans;
- provider charge reconciliation;
- workflow-level cost attribution.
