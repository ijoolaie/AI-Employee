"""Create the immutable cryptographic audit ledger envelope.

Revision ID: p0eimmutableaudit
Revises: rc9merge04, p8_08_agent_workforce
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "p0eimmutableaudit"
down_revision = ("rc9merge04", "p8_08_agent_workforce")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("ledger_scope", sa.String(length=80), nullable=True))
    op.add_column("audit_logs", sa.Column("ledger_sequence", sa.BigInteger(), nullable=True))
    op.add_column("audit_logs", sa.Column("previous_hash", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("entry_hash", sa.String(length=64), nullable=True))
    op.execute(
        "UPDATE audit_logs SET ledger_scope = COALESCE(tenant_id::text, '__platform__') WHERE ledger_scope IS NULL"
    )
    op.alter_column("audit_logs", "ledger_scope", nullable=False)
    op.create_index("ix_audit_logs_ledger_scope", "audit_logs", ["ledger_scope"])
    op.create_unique_constraint(
        "uq_audit_logs_ledger_scope_sequence",
        "audit_logs",
        ["ledger_scope", "ledger_sequence"],
    )
    op.create_unique_constraint("uq_audit_logs_entry_hash", "audit_logs", ["entry_hash"])
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_immutable_guard()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF OLD.entry_hash IS NOT NULL THEN
                RAISE EXCEPTION 'immutable audit ledger row cannot be modified or deleted';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_immutable_guard_trigger
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION audit_log_immutable_guard();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_immutable_guard_trigger ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_log_immutable_guard()")
    op.drop_constraint("uq_audit_logs_entry_hash", "audit_logs", type_="unique")
    op.drop_constraint("uq_audit_logs_ledger_scope_sequence", "audit_logs", type_="unique")
    op.drop_index("ix_audit_logs_ledger_scope", table_name="audit_logs")
    op.drop_column("audit_logs", "entry_hash")
    op.drop_column("audit_logs", "previous_hash")
    op.drop_column("audit_logs", "ledger_sequence")
    op.drop_column("audit_logs", "ledger_scope")
