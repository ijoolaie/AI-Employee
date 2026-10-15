"""Regression tests for tenant quota locking used by file uploads."""

import uuid

from sqlalchemy.dialects import postgresql

from app.services.file_service import _tenant_quota_lock_statement


def test_tenant_quota_lock_allows_foreign_key_key_share_checks():
    statement = _tenant_quota_lock_statement(uuid.uuid4())
    sql = str(statement.compile(dialect=postgresql.dialect()))

    # NO KEY UPDATE serializes quota checks for the same tenant while remaining
    # compatible with the KEY SHARE lock needed for tenant foreign-key inserts.
    assert "FOR NO KEY UPDATE" in sql
    assert "FOR KEY SHARE" not in sql
    assert "FOR UPDATE" not in sql
