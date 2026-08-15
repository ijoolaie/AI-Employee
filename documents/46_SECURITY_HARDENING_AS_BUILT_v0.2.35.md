# Security Hardening — As-Built v0.2.35

## Implemented
- Redis-backed request rate limiting with a tighter webhook bucket.
- Early Content-Length payload rejection; webhook bodies are also checked after reading.
- Webhook replay protection using a signed Unix timestamp and configurable skew window.
- Webhook signature now covers `timestamp + "." + raw_body`.
- Webhook secret rotation endpoint with encrypted-at-rest replacement and audit event.
- Secret rotation timestamp persisted for audit/operational visibility.
- Existing tenant/RBAC dependencies remain the authorization boundary for management endpoints.

## Verification status
- Static Python syntax: pending final release check.
- PostgreSQL migration execution: NOT VERIFIED in this environment.
- Redis rate-limit E2E: NOT VERIFIED without live Redis.
- Full pytest: NOT VERIFIED without all runtime services.

## Operational notes
- `RATE_LIMIT_FAIL_CLOSED=false` preserves availability if Redis is temporarily unavailable; production deployments may set it true.
- Webhook clients must send `X-Webhook-Timestamp` and sign `timestamp + "." + raw_body`.
- Existing webhook secrets are not recoverable from plaintext; rotation creates a new secret.
