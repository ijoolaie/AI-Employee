"""Add cross-tenant Skill Marketplace purchase records and buyer/owner separation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_cross_tenant"
down_revision = "w16_skill_mkt_publications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employee_skill_installations",
        sa.Column("source_owner_tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE employee_skill_installations "
            "SET source_owner_tenant_id = tenant_id "
            "WHERE source_owner_tenant_id IS NULL"
        )
    )
    op.alter_column("employee_skill_installations", "source_owner_tenant_id", nullable=False)
    op.drop_constraint(
        "fk_employee_skill_installations_skill_package_tenant",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_employee_skill_installations_source_package_tenant",
        "employee_skill_installations",
        "skill_packages",
        ["source_owner_tenant_id", "skill_package_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_employee_skill_installations_source_owner",
        "employee_skill_installations",
        ["source_owner_tenant_id"],
    )

    op.add_column(
        "skill_purchase_entitlements",
        sa.Column("source_owner_tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "skill_purchase_entitlements",
        sa.Column("source_publication_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE skill_purchase_entitlements "
            "SET source_owner_tenant_id = tenant_id "
            "WHERE source_owner_tenant_id IS NULL"
        )
    )
    op.alter_column("skill_purchase_entitlements", "source_owner_tenant_id", nullable=False)
    op.drop_constraint(
        "fk_skill_purchase_entitlement_package_tenant",
        "skill_purchase_entitlements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_skill_purchase_entitlement_source_owner_tenant",
        "skill_purchase_entitlements",
        "tenants",
        ["source_owner_tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_skill_purchase_entitlement_source_package_tenant",
        "skill_purchase_entitlements",
        "skill_packages",
        ["source_owner_tenant_id", "skill_package_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_skill_purchase_entitlement_source_publication",
        "skill_purchase_entitlements",
        "skill_marketplace_publications",
        ["source_publication_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_skill_purchase_entitlements_source_owner",
        "skill_purchase_entitlements",
        ["source_owner_tenant_id"],
    )
    op.create_index(
        "ix_skill_purchase_entitlements_source_publication",
        "skill_purchase_entitlements",
        ["source_publication_id"],
    )

    status_enum = postgresql.ENUM(
        "pending", "paid", "cancelled",
        name="skillmarketplacepurchasestatus",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_marketplace_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("buyer_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_deal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["buyer_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_purchases_buyer_tenant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["seller_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_purchases_seller_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"], ["skill_marketplace_publications.id"],
            name="fk_skill_marketplace_purchases_publication",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["buyer_tenant_id", "employee_id"],
            ["employees.tenant_id", "employees.id"],
            name="fk_skill_marketplace_purchases_buyer_employee_tenant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["seller_tenant_id", "skill_package_id"],
            ["skill_packages.tenant_id", "skill_packages.id"],
            name="fk_skill_marketplace_purchases_seller_package_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            name="fk_skill_marketplace_purchases_seller_product_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["business_deal_id"], ["business_deals.id"],
            name="fk_skill_marketplace_purchases_business_deal",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "buyer_tenant_id", "idempotency_key",
            name="uq_skill_marketplace_purchase_buyer_idempotency",
        ),
        sa.UniqueConstraint(
            "business_deal_id",
            name="uq_skill_marketplace_purchase_business_deal",
        ),
    )
    op.create_index(
        "ix_skill_marketplace_purchases_buyer_tenant_id",
        "skill_marketplace_purchases", ["buyer_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_seller_tenant_id",
        "skill_marketplace_purchases", ["seller_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_employee_id",
        "skill_marketplace_purchases", ["employee_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_skill_package_id",
        "skill_marketplace_purchases", ["skill_package_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_product_id",
        "skill_marketplace_purchases", ["product_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_buyer_status",
        "skill_marketplace_purchases", ["buyer_tenant_id", "status"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_seller",
        "skill_marketplace_purchases", ["seller_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_purchases_publication",
        "skill_marketplace_purchases", ["publication_id"],
    )
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) "
            "VALUES (gen_random_uuid(), 'skill_marketplace.purchase', "
            "'Core permission: skill_marketplace.purchase') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'Admin' AND p.code = 'skill_marketplace.purchase' "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'skill_marketplace.purchase')"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM permissions WHERE code = 'skill_marketplace.purchase'"
        )
    )
    op.drop_index("ix_skill_marketplace_purchases_publication", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_seller", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_buyer_status", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_product_id", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_skill_package_id", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_employee_id", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_seller_tenant_id", table_name="skill_marketplace_purchases")
    op.drop_index("ix_skill_marketplace_purchases_buyer_tenant_id", table_name="skill_marketplace_purchases")
    op.drop_table("skill_marketplace_purchases")
    postgresql.ENUM(name="skillmarketplacepurchasestatus").drop(op.get_bind(), checkfirst=True)

    op.execute(
        sa.text(
            "DO $ BEGIN "
            "IF EXISTS (SELECT 1 FROM skill_purchase_entitlements WHERE source_owner_tenant_id <> tenant_id) "
            "THEN RAISE EXCEPTION 'cannot downgrade: cross-tenant skill entitlements exist'; END IF; "
            "IF EXISTS (SELECT 1 FROM employee_skill_installations WHERE source_owner_tenant_id <> tenant_id) "
            "THEN RAISE EXCEPTION 'cannot downgrade: cross-tenant skill installations exist'; END IF; "
            "END $;"
        )
    )
    op.drop_index("ix_skill_purchase_entitlements_source_publication", table_name="skill_purchase_entitlements")
    op.drop_index("ix_skill_purchase_entitlements_source_owner", table_name="skill_purchase_entitlements")
    op.drop_constraint("fk_skill_purchase_entitlement_source_publication", "skill_purchase_entitlements", type_="foreignkey")
    op.drop_constraint("fk_skill_purchase_entitlement_source_package_tenant", "skill_purchase_entitlements", type_="foreignkey")
    op.drop_constraint("fk_skill_purchase_entitlement_source_owner_tenant", "skill_purchase_entitlements", type_="foreignkey")
    op.create_foreign_key(
        "fk_skill_purchase_entitlement_package_tenant",
        "skill_purchase_entitlements",
        "skill_packages",
        ["tenant_id", "skill_package_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.drop_column("skill_purchase_entitlements", "source_publication_id")
    op.drop_column("skill_purchase_entitlements", "source_owner_tenant_id")

    op.drop_index("ix_employee_skill_installations_source_owner", table_name="employee_skill_installations")
    op.drop_constraint(
        "fk_employee_skill_installations_source_package_tenant",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_employee_skill_installations_skill_package_tenant",
        "employee_skill_installations",
        "skill_packages",
        ["tenant_id", "skill_package_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.drop_column("employee_skill_installations", "source_owner_tenant_id")
