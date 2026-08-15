# Knowledge M9 Migration

The knowledge ingestion use-case now has a real domain/application boundary:
document and chunk models, repository/parser/embedding ports, application
service, event publication, infrastructure adapters, and isolated tests.

Existing RC8 parser/vector implementations remain behind adapters so callers
can migrate without a breaking rewrite.
