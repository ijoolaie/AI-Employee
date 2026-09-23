"""Add durable CEO-to-Internal-Manager delegation governance.

Revision ID: v1412workforcedelegations
Revises: v148whatsappidempotency
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v1412workforcedelegations"
down_revision = "v148whatsappidempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workforce_delegations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("manager_agent_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("delegated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scope", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("affected_employee_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("allowed_operations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("resource_limits", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("risk_tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="scheduled"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocation_conditions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workforce_delegations_tenant_status", "workforce_delegations", ["tenant_id", "status"])
    op.create_index("ix_workforce_delegations_manager", "workforce_delegations", ["tenant_id", "manager_agent_instance_id"])


def downgrade() -> None:
    op.drop_index("ix_workforce_delegations_manager", table_name="workforce_delegations")
    op.drop_index("ix_workforce_delegations_tenant_status", table_name="workforce_delegations")
    op.drop_table("workforce_delegations")
