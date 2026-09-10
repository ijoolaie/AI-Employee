"""Make TeamInstallation scope uniqueness NULL-safe.

Revision ID: p1gteaminstallnull
Revises: p1fshopifyoauthstate
"""
from alembic import op
import sqlalchemy as sa

revision = "p1gteaminstallnull"
down_revision = "p1fshopifyoauthstate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL UNIQUE constraints allow multiple NULL values. Replace the
    # nullable composite constraints with partial unique indexes so both the
    # default (NULL workspace) and named-workspace scopes are real invariants.
    op.drop_constraint(
        "uq_team_installations_tenant_version_workspace",
        "team_installations",
        type_="unique",
    )
    op.drop_constraint(
        "uq_team_installations_tenant_publication_workspace",
        "team_installations",
        type_="unique",
    )
    op.create_index(
        "uq_team_installations_tenant_version_workspace_null",
        "team_installations",
        ["tenant_id", "team_version_id"],
        unique=True,
        postgresql_where=sa.text("workspace_key IS NULL"),
    )
    op.create_index(
        "uq_team_installations_tenant_version_workspace",
        "team_installations",
        ["tenant_id", "team_version_id", "workspace_key"],
        unique=True,
        postgresql_where=sa.text("workspace_key IS NOT NULL"),
    )
    op.create_index(
        "uq_team_installations_tenant_publication_workspace_null",
        "team_installations",
        ["tenant_id", "source_publication_id"],
        unique=True,
        postgresql_where=sa.text(
            "source_publication_id IS NOT NULL AND workspace_key IS NULL"
        ),
    )
    op.create_index(
        "uq_team_installations_tenant_publication_workspace",
        "team_installations",
        ["tenant_id", "source_publication_id", "workspace_key"],
        unique=True,
        postgresql_where=sa.text(
            "source_publication_id IS NOT NULL AND workspace_key IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_team_installations_tenant_publication_workspace",
        table_name="team_installations",
    )
    op.drop_index(
        "uq_team_installations_tenant_publication_workspace_null",
        table_name="team_installations",
    )
    op.drop_index(
        "uq_team_installations_tenant_version_workspace",
        table_name="team_installations",
    )
    op.drop_index(
        "uq_team_installations_tenant_version_workspace_null",
        table_name="team_installations",
    )
    op.create_unique_constraint(
        "uq_team_installations_tenant_version_workspace",
        "team_installations",
        ["tenant_id", "team_version_id", "workspace_key"],
    )
    op.create_unique_constraint(
        "uq_team_installations_tenant_publication_workspace",
        "team_installations",
        ["tenant_id", "source_publication_id", "workspace_key"],
    )
