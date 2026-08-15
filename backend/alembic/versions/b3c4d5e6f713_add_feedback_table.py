"""Add feedback table — Phase 3 Validation tooling.

Revision ID: b3c4d5e6f713
Revises: 7a2b3c4d5e6f
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b3c4d5e6f713"
down_revision = "7a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=True
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id"),
            nullable=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=False, server_default="run"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
    )
    op.create_index("ix_feedback_tenant_id", "feedback", ["tenant_id"])
    op.create_index("ix_feedback_run_id", "feedback", ["run_id"])
    op.create_index("ix_feedback_employee_id", "feedback", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_employee_id", table_name="feedback")
    op.drop_index("ix_feedback_run_id", table_name="feedback")
    op.drop_index("ix_feedback_tenant_id", table_name="feedback")
    op.drop_table("feedback")
