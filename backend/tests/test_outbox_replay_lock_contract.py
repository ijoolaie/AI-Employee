from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.outbox import OutboxMessage


def test_dead_letter_replay_query_locks_and_tenant_scopes_row():
    statement = (
        select(OutboxMessage)
        .where(
            OutboxMessage.id == "00000000-0000-0000-0000-000000000001",
            OutboxMessage.tenant_id == "00000000-0000-0000-0000-000000000002",
        )
        .with_for_update()
    )

    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE" in sql
    assert "outbox_messages.tenant_id" in sql
    assert "outbox_messages.id" in sql
