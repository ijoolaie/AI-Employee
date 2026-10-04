"""W15 tenant-scoped cosmetic ownership ledger.

Revision ID: w15_cosmetic_entitlements
Revises: w14_employee_presentation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w15_cosmetic_entitlements"
down_revision = "w14_employee_presentation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cosmetic_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cosmetic_type", sa.String(length=32), nullable=False),
        sa.Column("cosmetic_value", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("source_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "cosmetic_type IN ('gender_presentation', 'outfit', 'hair_style', 'accessory')",
            name="ck_cosmetic_entitlement_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_cosmetic_entitlement_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_order_id"], ["business_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "employee_id",
            "product_id",
            name="uq_cosmetic_entitlement_tenant_employee_product",
        ),
    )
    op.create_index("ix_cosmetic_entitlements_tenant", "cosmetic_entitlements", ["tenant_id"])
    op.create_index("ix_cosmetic_entitlements_employee", "cosmetic_entitlements", ["employee_id"])
    op.create_index("ix_cosmetic_entitlements_product", "cosmetic_entitlements", ["product_id"])
    op.create_index("ix_cosmetic_entitlements_tenant_employee", "cosmetic_entitlements", ["tenant_id", "employee_id"])
    op.create_index("ix_cosmetic_entitlements_tenant_status", "cosmetic_entitlements", ["tenant_id", "status"])
    op.create_index("ix_cosmetic_entitlements_source_order", "cosmetic_entitlements", ["source_order_id"])


def downgrade():
    op.drop_index("ix_cosmetic_entitlements_source_order", table_name="cosmetic_entitlements")
    op.drop_index("ix_cosmetic_entitlements_tenant_status", table_name="cosmetic_entitlements")
    op.drop_index("ix_cosmetic_entitlements_tenant_employee", table_name="cosmetic_entitlements")
    op.drop_index("ix_cosmetic_entitlements_product", table_name="cosmetic_entitlements")
    op.drop_index("ix_cosmetic_entitlements_employee", table_name="cosmetic_entitlements")
    op.drop_index("ix_cosmetic_entitlements_tenant", table_name="cosmetic_entitlements")
    op.drop_table("cosmetic_entitlements")
