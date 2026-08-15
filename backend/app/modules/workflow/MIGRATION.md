# Workflow M8 Migration

The workflow execution use-case now has a real application service with:
- domain model
- repository port
- executor port
- event publication
- infrastructure adapters
- isolated unit tests

The legacy workflow engine remains behind `LegacyWorkflowExecutor` until all
existing callers are migrated. This is intentional compatibility protection.
