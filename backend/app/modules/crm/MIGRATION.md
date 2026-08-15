# CRM M10 Migration

CRM customer identity and conversation creation now have a real domain/application
boundary with repository and identity ports, event publication, infrastructure
adapters, and isolated tests.

The existing RC8 CRM implementation remains behind an adapter while callers
are migrated incrementally.
