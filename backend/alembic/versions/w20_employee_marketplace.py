"""W20 third-party Employee Marketplace foundation.

Revision ID: w20_employee_marketplace
Revises: w18_virtual_meeting_rooms
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w20_employee_marketplace"
down_revision = "w18_virtual_meeting_rooms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    package_status = postgresql.ENUM(
        "draft", "published", "suspended", "retired",
        name="employeemarketplacepackagestatus", create_type=False,
    )
    install_status = postgresql.ENUM(
        "active", "revoked",
        name="employeemarketplaceinstallationstatus", create_type=False,
    )
    package_status.create(op.get_bind(), checkfirst=True)
    install_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "employee_marketplace_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_agent_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", package_status, nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("risk_tier", sa.Integer(), nullable=False),
        sa.Column("employee_manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permission_manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("skill_package_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("workflow_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("visual_pack", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["owner_tenant_id", "source_agent_template_id"],
            ["agent_templates.tenant_id", "agent_templates.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_tenant_id", "slug", "version", name="uq_employee_marketplace_pkg_owner_slug_version"),
    )
    op.create_index("ix_employee_marketplace_pkg_owner_tenant_id", "employee_marketplace_packages", ["owner_tenant_id"])
    op.create_index("ix_employee_marketplace_pkg_owner_status", "employee_marketplace_packages", ["owner_tenant_id", "status"])
    op.create_index("ix_employee_marketplace_pkg_visibility", "employee_marketplace_packages", ["visibility"])

    op.create_table(
        "employee_marketplace_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("imported_agent_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("imported_agent_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sponsor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", install_status, nullable=False),
        sa.Column("provider_execution_status", sa.String(32), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["buyer_tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["employee_marketplace_packages.id"],
            name="fk_employee_marketplace_install_package",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["buyer_tenant_id", "imported_agent_template_id"],
            ["agent_templates.tenant_id", "agent_templates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["buyer_tenant_id", "imported_agent_definition_id"],
            ["agent_definitions.tenant_id", "agent_definitions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("buyer_tenant_id", "package_id", name="uq_employee_marketplace_install_buyer_package"),
    )
    op.create_index("ix_employee_marketplace_install_buyer_tenant_id", "employee_marketplace_installations", ["buyer_tenant_id"])
    op.create_index("ix_employee_marketplace_install_buyer_status", "employee_marketplace_installations", ["buyer_tenant_id", "status"])
    op.create_index("ix_employee_marketplace_install_package", "employee_marketplace_installations", ["package_id"])

    op.execute(sa.text(
        "INSERT INTO permissions (id, code, description) VALUES "
        "(gen_random_uuid(), 'employee_marketplace.publish', 'Publish a third-party Employee Marketplace package'), "
        "(gen_random_uuid(), 'employee_marketplace.install', 'Install a third-party Employee Marketplace package'), "
        "(gen_random_uuid(), 'employee_marketplace.revoke', 'Revoke a third-party Employee Marketplace installation') "
        "ON CONFLICT (code) DO NOTHING"
    ))
    op.execute(sa.text(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
        "WHERE r.name = 'Admin' AND p.code IN "
        "('employee_marketplace.publish','employee_marketplace.install','employee_marketplace.revoke') "
        "ON CONFLICT DO NOTHING"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM role_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE code IN "
        "('employee_marketplace.publish','employee_marketplace.install','employee_marketplace.revoke'))"
    ))
    op.execute(sa.text(
        "DELETE FROM permissions WHERE code IN "
        "('employee_marketplace.publish','employee_marketplace.install','employee_marketplace.revoke')"
    ))
    op.drop_index("ix_employee_marketplace_install_package", table_name="employee_marketplace_installations")
    op.drop_index("ix_employee_marketplace_install_buyer_status", table_name="employee_marketplace_installations")
    op.drop_index("ix_employee_marketplace_install_buyer_tenant_id", table_name="employee_marketplace_installations")
    op.drop_table("employee_marketplace_installations")
    op.drop_index("ix_employee_marketplace_pkg_visibility", table_name="employee_marketplace_packages")
    op.drop_index("ix_employee_marketplace_pkg_owner_status", table_name="employee_marketplace_packages")
    op.drop_index("ix_employee_marketplace_pkg_owner_tenant_id", table_name="employee_marketplace_packages")
    op.drop_table("employee_marketplace_packages")
    postgresql.ENUM(name="employeemarketplaceinstallationstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="employeemarketplacepackagestatus").drop(op.get_bind(), checkfirst=True)
