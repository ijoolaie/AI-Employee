"""Regression coverage for tenant-scoped outbox deduplication."""

import uuid

from sqlalchemy.dialects import postgresql

from app.services import outbox_service


def test_dedupe_lookup_binds_tenant_identity():
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    stmt_a = outbox_service._dedupe_lookup("same-key", tenant_a)
    stmt_b = outbox_service._dedupe_lookup("same-key", tenant_b)

    sql_a = str(stmt_a.compile(dialect=postgresql.dialect()))
    sql_b = str(stmt_b.compile(dialect=postgresql.dialect()))

    assert "tenant_id" in sql_a
    assert "tenant_id" in sql_b
    assert tenant_a in stmt_a.compile(dialect=postgresql.dialect()).params.values()
    assert tenant_b in stmt_b.compile(dialect=postgresql.dialect()).params.values()


def test_tenantless_dedupe_remains_global():
    stmt = outbox_service._dedupe_lookup("global-key", None)
    sql = str(stmt.compile(dialect=postgresql.dialect()))

    assert "tenant_id IS NULL" in sql
    assert "dedupe_key" in sql
