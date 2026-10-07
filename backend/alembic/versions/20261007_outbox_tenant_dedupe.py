"""Scope transactional outbox deduplication by tenant.

Revision ID: 20261007_outbox_tenant_dedupe
Revises: w21_ai_business_network
"""
from alembic import op
import sqlalchemy as sa

revision = "20261007_outbox_tenant_dedupe"
down_revision = "w21_ai_business_network"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_outbox_dedupe_key", table_name="outbox_messages")
    op.create_index(
        "uq_outbox_tenant_dedupe_key",
        "outbox_messages",
        ["tenant_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NOT NULL AND dedupe_key IS NOT NULL"),
    )
    op.create_index(
        "uq_outbox_global_dedupe_key",
        "outbox_messages",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL AND dedupe_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_outbox_global_dedupe_key", table_name="outbox_messages")
    op.drop_index("uq_outbox_tenant_dedupe_key", table_name="outbox_messages")
    op.create_index(
        "uq_outbox_dedupe_key",
        "outbox_messages",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )
