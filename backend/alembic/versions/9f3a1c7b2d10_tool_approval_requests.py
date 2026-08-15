"""add tool approval requests

Revision ID: 9f3a1c7b2d10
Revises: 677a41c87946
"""
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

revision = "9f3a1c7b2d10"
down_revision = "677a41c87946"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create global permission rows first; existing Admin roles receive them below.
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
    )
    for code, description in (
        ("approval.read", "Review pending Human Approval requests"),
        ("approval.decide", "Approve or reject Human Approval requests"),
    ):
        exists = op.get_bind().execute(sa.text("SELECT 1 FROM permissions WHERE code = :code"), {"code": code}).first()
        if exists is None:
            op.bulk_insert(permissions, [{"id": uuid.uuid4(), "code": code, "description": description}])
    op.create_table(
        "tool_approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("tool_call_id", sa.String(length=150), nullable=False),
        sa.Column("arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("continuation_messages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("iteration", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_approval_requests_tenant_id", "tool_approval_requests", ["tenant_id"])
    op.create_index("ix_tool_approval_requests_run_id", "tool_approval_requests", ["run_id"])
    op.create_index("ix_tool_approval_requests_status", "tool_approval_requests", ["status"])
    op.create_index("ix_tool_approval_requests_created_at", "tool_approval_requests", ["created_at"])
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.name = 'Admin' AND p.code IN ('approval.read', 'approval.decide')
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    op.drop_index("ix_tool_approval_requests_created_at", table_name="tool_approval_requests")
    op.drop_index("ix_tool_approval_requests_status", table_name="tool_approval_requests")
    op.drop_index("ix_tool_approval_requests_run_id", table_name="tool_approval_requests")
    op.drop_index("ix_tool_approval_requests_tenant_id", table_name="tool_approval_requests")
    op.drop_table("tool_approval_requests")
