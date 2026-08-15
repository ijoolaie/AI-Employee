"""RC3 customer CRM, WhatsApp channel and conversation linkage."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "fd4e5f6a7b89"
down_revision = "fc3d4e5f6a78"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_key", sa.String(160), nullable=False),
        sa.Column("name", sa.String(160)), sa.Column("email", sa.String(320)), sa.Column("phone", sa.String(40)),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("notes", sa.Text()), sa.Column("last_channel", sa.String(40)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "external_key", name="uq_customers_tenant_external_key"))
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.add_column("customer_conversations", sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_customer_conversations_customer", "customer_conversations", "customers", ["customer_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_customer_conversations_customer_id", "customer_conversations", ["customer_id"])
    op.alter_column("customer_channels", "channel_type", existing_type=sa.String(length=30), nullable=False)

def downgrade():
    op.drop_index("ix_customer_conversations_customer_id", table_name="customer_conversations")
    op.drop_constraint("fk_customer_conversations_customer", "customer_conversations", type_="foreignkey")
    op.drop_column("customer_conversations", "customer_id")
    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_index("ix_customers_email", table_name="customers")
    op.drop_index("ix_customers_tenant_id", table_name="customers")
    op.drop_table("customers")
