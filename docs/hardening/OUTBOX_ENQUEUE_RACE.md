# Outbox enqueue concurrency hardening

The outbox deduplication contract uses a unique database index on `dedupe_key`. The enqueue path must treat the initial lookup as an optimization only: concurrent workers can both observe no row and race to INSERT.

The durable correctness boundary is the unique constraint. A losing transaction must recover inside a SAVEPOINT, re-read the existing row, and return it rather than surfacing an avoidable integrity error.
