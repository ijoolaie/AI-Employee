"""W16 versioned skill packages and tenant installation ledger.
Revision ID: w16_skill_marketplace
Revises: w15_cosmetic_entitlements
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_marketplace"
down_revision = "w15_cosmetic_entitlements"
branch_labels = None
depends_on = None


def upgrade():
    skill_status = postgresql.ENUM("draft", "published", "suspended", "retired", name="skillpackagestatus")
    install_status = postgresql.ENUM("active", "revoked", name="employeeskillinstallationstatus")
    skill_status.create(op.get_bind(), checkfirst=True)
    install_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", skill_status, nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("compatibility", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("presentation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", "version", name="uq_skill_packages_tenant_slug_version"),
    )
    op.create_index("ix_skill_packages_tenant_id", "skill_packages", ["tenant_id"])
    op.create_index("ix_skill_packages_tenant_status", "skill_packages", ["tenant_id", "status"])
    op.create_index("ix_skill_packages_product", "skill_packages", ["tenant_id", "product_id"])

    op.create_table(
        "employee_skill_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", install_status, nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_package_id"], ["skill_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "employee_id", "skill_package_id", name="uq_employee_skill_installation"),
    )
    op.create_index("ix_employee_skill_installations_tenant_id", "employee_skill_installations", ["tenant_id"])
    op.create_index("ix_employee_skill_installations_employee_id", "employee_skill_installations", ["employee_id"])
    op.create_index("ix_employee_skill_installations_skill_package_id", "employee_skill_installations", ["skill_package_id"])
    op.create_index("ix_employee_skill_installations_tenant_employee", "employee_skill_installations", ["tenant_id", "employee_id"])
    op.create_index("ix_employee_skill_installations_tenant_status", "employee_skill_installations", ["tenant_id", "status"])


def downgrade():
    op.drop_index("ix_employee_skill_installations_tenant_status", table_name="employee_skill_installations")
    op.drop_index("ix_employee_skill_installations_tenant_employee", table_name="employee_skill_installations")
    op.drop_index("ix_employee_skill_installations_skill_package_id", table_name="employee_skill_installations")
    op.drop_index("ix_employee_skill_installations_employee_id", table_name="employee_skill_installations")
    op.drop_index("ix_employee_skill_installations_tenant_id", table_name="employee_skill_installations")
    op.drop_table("employee_skill_installations")
    op.drop_index("ix_skill_packages_product", table_name="skill_packages")
    op.drop_index("ix_skill_packages_tenant_status", table_name="skill_packages")
    op.drop_index("ix_skill_packages_tenant_id", table_name="skill_packages")
    op.drop_table("skill_packages")
    sa.Enum(name="employeeskillinstallationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="skillpackagestatus").drop(op.get_bind(), checkfirst=True)
