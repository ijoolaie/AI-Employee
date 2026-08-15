"""Add SaaS sales-readiness foundations: onboarding, products, integrations and human handoff."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "fc3d4e5f6a78"
down_revision = ("c2d3e4f5a6b9", "fb2c3d4e5f67")
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(80)), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("category", sa.String(120)),
        sa.Column("price", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="EUR"),
        sa.Column("inventory", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("images", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_tenant_active", "products", ["tenant_id", "is_active"])
    op.create_table("commerce_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False), sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_commerce_integrations_tenant", "commerce_integrations", ["tenant_id"])
    op.create_table("onboarding_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed_steps", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("business_type", sa.String(80)), sa.Column("setup_data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_onboarding_progress_tenant_id", "onboarding_progress", ["tenant_id"], unique=True)
    op.add_column("customer_conversations", sa.Column("handoff_requested", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("customer_conversations", sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_customer_conversations_assigned_user", "customer_conversations", "users", ["assigned_user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_customer_conversations_assigned_user_id", "customer_conversations", ["assigned_user_id"])

def downgrade():
    op.drop_index("ix_customer_conversations_assigned_user_id", table_name="customer_conversations")
    op.drop_constraint("fk_customer_conversations_assigned_user", "customer_conversations", type_="foreignkey")
    op.drop_column("customer_conversations", "assigned_user_id")
    op.drop_column("customer_conversations", "handoff_requested")
    op.drop_index("ix_onboarding_progress_tenant_id", table_name="onboarding_progress")
    op.drop_table("onboarding_progress")
    op.drop_index("ix_commerce_integrations_tenant", table_name="commerce_integrations")
    op.drop_table("commerce_integrations")
    op.drop_index("ix_products_tenant_active", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_table("products")
