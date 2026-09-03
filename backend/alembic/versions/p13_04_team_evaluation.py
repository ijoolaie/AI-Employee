"""Create immutable TeamEvaluation evidence records.

Revision ID: p13_04_team_evaluation
Revises: p13_02_team_install_boundary
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p13_04_team_evaluation"
down_revision = "p13_02_team_install_boundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evaluation_type", sa.String(length=80), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_class", sa.String(length=32), nullable=False),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["team_version_id"], ["team_versions.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_team_evaluations_tenant_id", "team_evaluations", ["tenant_id"])
    op.create_index("ix_team_evaluations_team_version_id", "team_evaluations", ["team_version_id"])


def downgrade() -> None:
    op.drop_index("ix_team_evaluations_team_version_id", table_name="team_evaluations")
    op.drop_index("ix_team_evaluations_tenant_id", table_name="team_evaluations")
    op.drop_table("team_evaluations")
