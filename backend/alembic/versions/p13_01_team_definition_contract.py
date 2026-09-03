"""Phase 13.1 Agent Team definition/version contract.

Revision ID: p13_01_team_definition_contract
Revises: p12_05_test_run_expiry_index
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p13_01_team_definition_contract"
down_revision = "p12_05_test_run_expiry_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_team_definitions_tenant_slug"),
    )
    op.create_index("ix_team_definitions_tenant_id", "team_definitions", ["tenant_id"])

    op.create_table(
        "team_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("member_agent_definition_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("execution_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allowed_tools", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["team_definitions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "version", name="uq_team_versions_team_version"),
    )
    op.create_index("ix_team_versions_team_id", "team_versions", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_team_versions_team_id", table_name="team_versions")
    op.drop_table("team_versions")
    op.drop_index("ix_team_definitions_tenant_id", table_name="team_definitions")
    op.drop_table("team_definitions")
