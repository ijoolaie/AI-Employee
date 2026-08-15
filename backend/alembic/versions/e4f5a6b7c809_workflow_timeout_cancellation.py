"""Workflow timeout and cancellation support.
Revision ID: e4f5a6b7c809
Revises: d3e4f5a6b708
"""
from alembic import op
import sqlalchemy as sa
revision = "e4f5a6b7c809"
down_revision = "d3e4f5a6b708"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("workflow_runs", sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workflow_runs", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workflow_runs", sa.Column("cancel_reason", sa.Text(), nullable=True))
    op.create_index("ix_workflow_runs_deadline_at", "workflow_runs", ["deadline_at"])
    op.execute("INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), 'workflow.cancel', 'Cancel workflow runs') ON CONFLICT (code) DO NOTHING")
    op.execute("INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.name = 'Admin' AND p.code = 'workflow.cancel' AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)")

def downgrade() -> None:
    op.execute("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code='workflow.cancel')")
    op.execute("DELETE FROM permissions WHERE code='workflow.cancel'")
    op.drop_index("ix_workflow_runs_deadline_at", table_name="workflow_runs")
    op.drop_column("workflow_runs", "cancel_reason")
    op.drop_column("workflow_runs", "cancelled_at")
    op.drop_column("workflow_runs", "deadline_at")
