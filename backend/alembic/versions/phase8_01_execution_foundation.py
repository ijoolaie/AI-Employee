"""Phase 8.2 unified execution foundation persistence.

Revision ID: p8_01_execution
Revises: v14007refundauth
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_01_execution"
down_revision = "v14007refundauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executor_type = postgresql.ENUM("human", "agent", name="executortype", create_type=False)
    work_status = postgresql.ENUM(
        "draft", "ready", "assigned", "running", "succeeded", "failed",
        "blocked", "cancelled", "waiting_approval",
        name="workitemstatus",
        create_type=False,
    )
    agent_status = postgresql.ENUM(
        "enabled", "disabled", "draining",
        name="agentinstancestatus",
        create_type=False,
    )

    executor_type.create(op.get_bind(), checkfirst=True)
    work_status.create(op.get_bind(), checkfirst=True)
    agent_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("allowed_tools", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("model_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("input_schema", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_schema", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("policy_requirements", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_agent_definitions_tenant_slug"),
    )

    op.create_table(
        "agent_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", agent_status, nullable=False, server_default="enabled"),
        sa.Column("max_concurrency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("budget_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "work_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", work_status, nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("executor_type", executor_type),
        sa.Column("executor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("input_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_data", postgresql.JSONB()),
        sa.Column("policy_context", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("parent_work_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("work_items.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_work_items_tenant_idempotency"),
    )

    op.create_index("ix_agent_instances_tenant_definition", "agent_instances", ["tenant_id", "agent_definition_id"])
    op.create_index("ix_work_items_tenant_status", "work_items", ["tenant_id", "status"])
    op.create_index("ix_work_items_tenant_executor", "work_items", ["tenant_id", "executor_type", "executor_id"])


def downgrade() -> None:
    op.drop_index("ix_work_items_tenant_executor", table_name="work_items")
    op.drop_index("ix_work_items_tenant_status", table_name="work_items")
    op.drop_index("ix_agent_instances_tenant_definition", table_name="agent_instances")
    op.drop_table("work_items")
    op.drop_table("agent_instances")
    op.drop_table("agent_definitions")
    sa.Enum(name="agentinstancestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="workitemstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="executortype").drop(op.get_bind(), checkfirst=True)
