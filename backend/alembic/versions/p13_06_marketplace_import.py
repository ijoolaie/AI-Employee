"""Add marketplace publication provenance to team installations.

Revision ID: p13_06_marketplace_import
Revises: p13_05_marketplace_boundary
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p13_06_marketplace_import"
down_revision = "p13_05_marketplace_boundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "team_installations",
        sa.Column("source_publication_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_team_installations_source_publication",
        "team_installations",
        "marketplace_publications",
        ["source_publication_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_team_installations_source_publication_id",
        "team_installations",
        ["source_publication_id"],
    )
    op.create_unique_constraint(
        "uq_team_installations_tenant_publication_workspace",
        "team_installations",
        ["tenant_id", "source_publication_id", "workspace_key"],
    )
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) "
            "VALUES (gen_random_uuid(), 'marketplace.install', 'Core permission: marketplace.install') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'Admin' AND p.code = 'marketplace.install' "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'marketplace.install')"
        )
    )
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'marketplace.install'"))
    op.drop_constraint("uq_team_installations_tenant_publication_workspace", "team_installations", type_="unique")
    op.drop_index("ix_team_installations_source_publication_id", table_name="team_installations")
    op.drop_constraint("fk_team_installations_source_publication", "team_installations", type_="foreignkey")
    op.drop_column("team_installations", "source_publication_id")
