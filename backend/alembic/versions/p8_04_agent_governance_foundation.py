"""Stage 8 workforce governance foundation for AgentTemplate and governed instances.

Revision ID: p8_04_agent_governance
Revises: p8_03_agent_binding
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_04_agent_governance"
down_revision = "p8_03_agent_binding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    agent_template_status = postgresql.ENUM(
        "draft", "active", "retired", name="agenttemplatestatus", create_type=False
    )
    agent_template_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", agent_template_status, nullable=False, server_default="draft"),
        sa.Column("risk_tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capability_contract", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("permission_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("approval_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evaluation_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("install_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", "version", name="uq_agent_templates_tenant_slug_version"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["agent_definition_id"], ["agent_definitions.id"]),
    )


def downgrade() -> None:
    op.drop_table("agent_templates")
    postgresql.ENUM("draft", "active", "retired", name="agenttemplatestatus").drop(
        op.get_bind(), checkfirst=True
    )
