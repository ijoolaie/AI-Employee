"""Phase 13.2 tenant-local Agent Team installation boundary.

Revision ID: p13_02_team_install_boundary
Revises: p13_01_team_definition_contract
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p13_02_team_install_boundary"
down_revision = "p13_01_team_definition_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_key", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("installed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["team_version_id"], ["team_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "team_version_id", "workspace_key",
            name="uq_team_installations_tenant_version_workspace",
        ),
    )
    op.create_index("ix_team_installations_tenant_id", "team_installations", ["tenant_id"])
    op.create_index("ix_team_installations_team_version_id", "team_installations", ["team_version_id"])


def downgrade() -> None:
    op.drop_index("ix_team_installations_team_version_id", table_name="team_installations")
    op.drop_index("ix_team_installations_tenant_id", table_name="team_installations")
    op.drop_table("team_installations")
