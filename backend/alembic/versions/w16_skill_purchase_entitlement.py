"""Add verified commercial purchase entitlements for W16 skills."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_purchase_entitlement"
down_revision = "w16_skill_package_immutability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "active", "revoked",
        name="skillpurchaseentitlementstatus",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_purchase_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_package_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_order_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "tenant_id", "employee_id", "skill_package_id",
            name="uq_skill_purchase_entitlement",
        ),
        sa.UniqueConstraint(
            "provider", "provider_event_id",
            name="uq_skill_purchase_entitlement_provider_event",
        ),
    )
    op.create_index(
        "ix_skill_purchase_entitlements_tenant_employee",
        "skill_purchase_entitlements",
        ["tenant_id", "employee_id"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_tenant_status",
        "skill_purchase_entitlements",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_tenant_id",
        "skill_purchase_entitlements",
        ["tenant_id"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_employee_id",
        "skill_purchase_entitlements",
        ["employee_id"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_skill_package_id",
        "skill_purchase_entitlements",
        ["skill_package_id"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_source_order_id",
        "skill_purchase_entitlements",
        ["source_order_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_skill_purchase_entitlement_provider_event",
        "skill_purchase_entitlements",
        type_="unique",
    )
    op.drop_index("ix_skill_purchase_entitlements_source_order_id", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_skill_package_id", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_employee_id", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_tenant_id", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_tenant_status", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_tenant_employee", table_name="skill_purchase_entitlements")
    op.drop_table("skill_purchase_entitlements")
    postgresql.ENUM(name="skillpurchaseentitlementstatus").drop(op.get_bind(), checkfirst=True)
