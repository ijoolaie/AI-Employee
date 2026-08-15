# Package Changelog v1.9

## v0.2.31.1

Maintenance/reconciliation release after the v0.2.31 As-Built audit.

- Added transactional outbox and post-commit Celery dispatch.
- Hardened workflow, schedule, event and human-approval resume paths.
- Moved SMTP delivery behind the durable outbox.
- Added encrypted-at-rest webhook secret support for newly created triggers.
- Reconciled Tenant Admin default permissions.
- Updated package/application version.
- Rebuilt release verification metadata and explicitly removed cache/bytecode artifacts.
