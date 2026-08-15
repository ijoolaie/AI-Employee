# RC8 P0-P4 — Password Recovery

Implemented secure tenant-scoped password recovery.

- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- single-use 48-byte random tokens stored only as SHA-256 hashes
- 30-minute expiration by default
- generic response to prevent account enumeration
- request rate limiting per account/window
- durable transactional email via the existing outbox/SMTP worker
- reset token cleanup and one-time use enforcement
- password change timestamp invalidates previously issued JWT sessions
- audit events for request and completion
- frontend `/forgot-password` and `/reset-password` pages
- migration: `rc8p0p4pwd`

Runtime SMTP delivery and database migration must still be validated in staging.
