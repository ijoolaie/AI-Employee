# M3 — Infrastructure Boundary Migration

## Completed
- Repository and Unit-of-Work ports
- Queue and event-bus ports
- Object-storage port
- AI, payment, and commerce provider ports
- Per-module port files
- Adapter boundaries for SQLAlchemy, Redis, Celery, storage, Stripe, Shopify, and AI
- Composition-root contract
- Architecture tests

## Safety
M3 is intentionally structural. Existing RC8 implementations remain in place;
no public API, database schema, or runtime behavior is intentionally changed.

## Next migration
Move concrete implementations behind these ports one adapter at a time, run
the existing test suite after each move, then remove direct infrastructure
construction from application modules.
