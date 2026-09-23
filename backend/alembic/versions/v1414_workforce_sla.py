"""Create tenant-owned workforce SLA contracts.

Revision ID: v1414workforcesla
Revises: v1413workforceprovenance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v1414workforcesla"
down_revision = "v1413workforceprovenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workforce_sla_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("max_queue_age_seconds", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", name="uq_workforce_sla_contract_tenant"),
    )
    op.create_index("ix_workforce_sla_contracts_tenant_id", "workforce_sla_contracts", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_workforce_sla_contracts_tenant_id", table_name="workforce_sla_contracts")
    op.drop_table("workforce_sla_contracts")
