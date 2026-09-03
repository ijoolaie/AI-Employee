"""Create marketplace publication boundary.

Revision ID: p13_05_marketplace_boundary
Revises: p13_04_team_evaluation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p13_05_marketplace_boundary"
down_revision = "p13_04_team_evaluation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplace_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("owner_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=2000), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_version_id"], ["team_versions.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("team_version_id", name="uq_marketplace_publications_team_version"),
    )
    op.create_index("ix_marketplace_publications_owner_tenant_id", "marketplace_publications", ["owner_tenant_id"])
    op.create_index("ix_marketplace_publications_team_version_id", "marketplace_publications", ["team_version_id"])
    op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), 'marketplace.publish', 'Core permission: marketplace.publish') ON CONFLICT (code) DO NOTHING"))
    op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), 'marketplace.read', 'Core permission: marketplace.read') ON CONFLICT (code) DO NOTHING"))
    op.execute(sa.text("INSERT INTO role_permissions (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.name = 'Admin' AND p.code IN ('marketplace.publish', 'marketplace.read') ON CONFLICT DO NOTHING"))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ('marketplace.publish', 'marketplace.read'))"))
    op.execute(sa.text("DELETE FROM permissions WHERE code IN ('marketplace.publish', 'marketplace.read')"))
    op.drop_index("ix_marketplace_publications_team_version_id", table_name="marketplace_publications")
    op.drop_index("ix_marketplace_publications_owner_tenant_id", table_name="marketplace_publications")
    op.drop_table("marketplace_publications")
