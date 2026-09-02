"""Phase 12.1-12.3 Test Center foundation.

Revision ID: p12_01_test_center
Revises: rc9merge01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p12_01_test_center"
down_revision = "rc9merge01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("test_type", sa.String(length=50), nullable=False, server_default="acceptance"),
        sa.Column("category", sa.String(length=80), nullable=False, server_default="backend"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workspace_key", sa.String(length=120), nullable=True),
        sa.Column("prerequisites", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("expected_result", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_requirements", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_test_definitions_tenant_code"),
    )
    op.create_index("ix_test_definitions_tenant_workspace", "test_definitions", ["tenant_id", "workspace_key"])
    op.create_index("ix_test_definitions_tenant_enabled", "test_definitions", ["tenant_id", "enabled"])

    test_run_status = postgresql.ENUM(
        "queued", "running", "passed", "failed", "cancelled", "expired",
        name="testrunstatus",
        create_type=False,
    )
    test_run_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "test_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_key", sa.String(length=120), nullable=True),
        sa.Column("status", test_run_status, nullable=False, server_default="queued"),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("executor_type", sa.String(length=30), nullable=False, server_default="backend"),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fixtures", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("correlation_id", name="uq_test_runs_correlation_id"),
    )
    op.create_index("ix_test_runs_tenant_created", "test_runs", ["tenant_id", "created_at"])
    op.create_index("ix_test_runs_tenant_status", "test_runs", ["tenant_id", "status"])
    op.create_index("ix_test_runs_tenant_definition", "test_runs", ["tenant_id", "test_definition_id"])
    op.create_index("ix_test_runs_tenant_workspace", "test_runs", ["tenant_id", "workspace_key"])


def downgrade() -> None:
    op.drop_index("ix_test_runs_tenant_workspace", table_name="test_runs")
    op.drop_index("ix_test_runs_tenant_definition", table_name="test_runs")
    op.drop_index("ix_test_runs_tenant_status", table_name="test_runs")
    op.drop_index("ix_test_runs_tenant_created", table_name="test_runs")
    op.drop_table("test_runs")
    sa.Enum(name="testrunstatus").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_test_definitions_tenant_enabled", table_name="test_definitions")
    op.drop_index("ix_test_definitions_tenant_workspace", table_name="test_definitions")
    op.drop_table("test_definitions")
