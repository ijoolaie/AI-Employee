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
    template_status = postgresql.ENUM(
        "draft", "evaluating", "published", "suspended", "retired",
        name="agenttemplatestatus", create_type=False,
    )
    template_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id"), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", template_status, nullable=False, server_default="draft"),
        sa.Column("risk_tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capability_contract", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("permission_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("approval_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evaluation_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("install_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "slug", "version", name="uq_agent_templates_tenant_slug_version"),
    )
    op.create_index("ix_agent_templates_tenant_status", "agent_templates", ["tenant_id", "status"])
    op.create_index("ix_agent_templates_agent_definition_id", "agent_templates", ["agent_definition_id"])

    op.add_column("agent_instances", sa.Column("agent_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("agent_instances", sa.Column("sponsor_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("agent_instances", sa.Column("permission_policy", postgresql.JSONB(), nullable=False, server_default="{}"))
    op.add_column("agent_instances", sa.Column("approval_policy", postgresql.JSONB(), nullable=False, server_default="{}"))
    op.add_column("agent_instances", sa.Column("risk_tier", sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key(
        None,
        "agent_instances",
        "agent_templates",
        ["agent_template_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        None,
        "agent_instances",
        "users",
        ["sponsor_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_agent_instances_agent_template_id", "agent_instances", ["agent_template_id"])
    op.create_index("ix_agent_instances_sponsor_user_id", "agent_instances", ["sponsor_user_id"])

    op.execute(sa.text("ALTER TYPE agentinstancestatus ADD VALUE IF NOT EXISTS 'suspended'"))
    op.execute(sa.text("ALTER TYPE agentinstancestatus ADD VALUE IF NOT EXISTS 'retired'"))


def downgrade() -> None:
    op.drop_index("ix_agent_instances_sponsor_user_id", table_name="agent_instances")
    op.drop_index("ix_agent_instances_agent_template_id", table_name="agent_instances")
    op.drop_constraint("agent_instances_sponsor_user_id_fkey", "agent_instances", type_="foreignkey")
    op.drop_constraint("agent_instances_agent_template_id_fkey", "agent_instances", type_="foreignkey")
    op.drop_column("agent_instances", "risk_tier")
    op.drop_column("agent_instances", "approval_policy")
    op.drop_column("agent_instances", "permission_policy")
    op.drop_column("agent_instances", "sponsor_user_id")
    op.drop_column("agent_instances", "agent_template_id")
    op.drop_index("ix_agent_templates_agent_definition_id", table_name="agent_templates")
    op.drop_index("ix_agent_templates_tenant_status", table_name="agent_templates")
    op.drop_table("agent_templates")
    template_status = postgresql.ENUM(name="agenttemplatestatus")
    template_status.drop(op.get_bind(), checkfirst=True)
