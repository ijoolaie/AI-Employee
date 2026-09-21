"""Add edition-aware scope metadata to Test Center definitions.

Revision ID: p12_06_test_definition_scope
Revises: v148whatsappidempotency
"""

from alembic import op
import sqlalchemy as sa


revision = "p12_06_test_definition_scope"
down_revision = "v148whatsappidempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("test_definitions", sa.Column("edition", sa.String(length=20), nullable=False, server_default="shared"))
    op.add_column("test_definitions", sa.Column("service_group", sa.String(length=80), nullable=False, server_default="shared"))
    op.add_column("test_definitions", sa.Column("scope_type", sa.String(length=40), nullable=False, server_default="same_tenant"))
    op.add_column("test_definitions", sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="low"))
    op.create_index("ix_test_definitions_tenant_edition", "test_definitions", ["tenant_id", "edition"])


def downgrade() -> None:
    op.drop_index("ix_test_definitions_tenant_edition", table_name="test_definitions")
    op.drop_column("test_definitions", "risk_level")
    op.drop_column("test_definitions", "scope_type")
    op.drop_column("test_definitions", "service_group")
    op.drop_column("test_definitions", "edition")
