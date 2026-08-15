"""Memory lifecycle, versioning, and supersession.

Revision ID: e8a1c4d7b902
Revises: d4e7f1a9b302
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e8a1c4d7b902"
down_revision = "d4e7f1a9b302"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employee_memories", sa.Column("supersedes_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("employee_memories", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("employee_memories", sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(sa.text("UPDATE employee_memories SET effective_at = created_at WHERE effective_at IS NULL"))
    op.alter_column("employee_memories", "effective_at", nullable=False)
    op.create_index("ix_employee_memories_supersedes_id", "employee_memories", ["supersedes_id"])
    op.create_foreign_key("fk_employee_memories_supersedes_id", "employee_memories", "employee_memories", ["supersedes_id"], ["id"], ondelete="SET NULL")
    op.execute(sa.text("ALTER TABLE employee_memories DROP CONSTRAINT IF EXISTS employee_memories_status_check"))
    op.create_check_constraint("employee_memories_status_check", "employee_memories", "status IN ('active','superseded','expired','deleted','conflict')")


def downgrade() -> None:
    op.drop_constraint("employee_memories_status_check", "employee_memories", type_="check")
    op.drop_constraint("fk_employee_memories_supersedes_id", "employee_memories", type_="foreignkey")
    op.drop_index("ix_employee_memories_supersedes_id", table_name="employee_memories")
    op.drop_column("employee_memories", "effective_at")
    op.drop_column("employee_memories", "version")
    op.drop_column("employee_memories", "supersedes_id")
