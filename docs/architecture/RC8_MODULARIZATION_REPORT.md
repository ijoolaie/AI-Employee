# RC8 Modularization Report

**Status: M1 implemented**

### Changed
- Report, Document, Invoice, Order, and Sales Employee implementations
  moved into bounded module directories.
- Legacy service imports remain compatible through facades.
- Employee manifests and an explicit registry were added.
- Shared contracts/events were introduced as a deliberately small kernel.
- Architecture tests were added.

### Intentionally unchanged
- Database schema and Alembic migrations.
- Public API paths.
- Existing worker/tool entry points.
- Existing frontend routes.
- Business behavior.

This is a low-risk structural migration. M2 should extract the remaining
bounded contexts after their real import graphs are reviewed.
