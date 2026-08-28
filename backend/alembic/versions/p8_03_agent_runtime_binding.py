"""Phase 8.3 explicit AgentDefinition -> EmployeeVersion runtime binding."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_03_agent_binding"
down_revision = "p8_01_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runtime_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id"), nullable=False),
        sa.Column("employee_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employee_versions.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "agent_definition_id", name="uq_agent_runtime_binding_agent"),
    )
    op.create_index("ix_agent_runtime_bindings_tenant_id", "agent_runtime_bindings", ["tenant_id"])
    op.create_index("ix_agent_runtime_bindings_agent_definition_id", "agent_runtime_bindings", ["agent_definition_id"])
    op.create_index("ix_agent_runtime_bindings_employee_version_id", "agent_runtime_bindings", ["employee_version_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_runtime_bindings_employee_version_id", table_name="agent_runtime_bindings")
    op.drop_index("ix_agent_runtime_bindings_agent_definition_id", table_name="agent_runtime_bindings")
    op.drop_index("ix_agent_runtime_bindings_tenant_id", table_name="agent_runtime_bindings")
    op.drop_table("agent_runtime_bindings")
