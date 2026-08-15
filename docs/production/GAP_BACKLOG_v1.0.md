# Gap Backlog v1.0 — Remaining Before Final Verification

## P0 — Must be closed before Phase 7
- Provision network-enabled CI/staging environment.
- Install backend/frontend locked dependencies.
- Configure PostgreSQL, Redis and Celery.
- Configure real provider credentials in the secret manager.
- Configure HTTPS/TLS.
- Execute migration and rollback rehearsal.
- Confirm backup storage and restore target.

## P1 — Final environment configuration
- Complete Stripe certification configuration.
- Complete Shopify OAuth/webhook configuration.
- Select and configure the WhatsApp outbound provider adapter.
- Configure production monitoring and alerting.
- Configure support/incident ownership.

## P2 — Optional post-v1.0 improvements
- Full translation coverage of every UI string.
- Provider credential rotation UI backed by a dedicated secret-management service.
- Advanced provider failover/routing policy.
- Expanded admin analytics.

## Explicitly deferred to Phase 7
Testing is intentionally not performed as a development gate in Phases 0–6. The final sweep is the only release certification gate.
