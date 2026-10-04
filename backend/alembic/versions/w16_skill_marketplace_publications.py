"""Add immutable third-party SkillPackage marketplace publications."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_marketplace_publications"
down_revision = "w16_skill_purchase_entitlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_marketplace_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("owner_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False, server_default="private"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=2000), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_tenant_id"],
            ["tenants.id"],
            name="fk_skill_marketplace_publications_owner_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_skill_marketplace_publications_package_tenant",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "skill_package_id",
            name="uq_skill_marketplace_publications_skill_package",
        ),
    )
    op.create_index(
        "ix_skill_marketplace_publications_owner_tenant",
        "skill_marketplace_publications",
        ["owner_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_publications_visibility",
        "skill_marketplace_publications",
        ["visibility"],
    )
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) "
            "VALUES (gen_random_uuid(), 'skill_marketplace.publish', "
            "'Core permission: skill_marketplace.publish') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) "
            "VALUES (gen_random_uuid(), 'skill_marketplace.read', "
            "'Core permission: skill_marketplace.read') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'Admin' "
            "AND p.code IN ('skill_marketplace.publish', 'skill_marketplace.read') "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions "
            "WHERE code IN ('skill_marketplace.publish', 'skill_marketplace.read'))"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM permissions "
            "WHERE code IN ('skill_marketplace.publish', 'skill_marketplace.read')"
        )
    )
    op.drop_index(
        "ix_skill_marketplace_publications_visibility",
        table_name="skill_marketplace_publications",
    )
    op.drop_index(
        "ix_skill_marketplace_publications_owner_tenant",
        table_name="skill_marketplace_publications",
    )
    op.drop_table("skill_marketplace_publications")
