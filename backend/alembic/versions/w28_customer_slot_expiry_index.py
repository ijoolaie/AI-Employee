"""Index tenant-wide expiry scans for bounded customer slot cleanup."""

from alembic import op

revision = "w28_customer_slot_expiry_index"
down_revision = "w27_product_inventory_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_customer_conversation_slots_expiry",
        table_name="customer_conversation_slots",
    )
    op.create_index(
        "ix_customer_conversation_slots_tenant_expiry",
        "customer_conversation_slots",
        ["tenant_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_conversation_slots_tenant_expiry",
        table_name="customer_conversation_slots",
    )
    op.create_index(
        "ix_customer_conversation_slots_expiry",
        "customer_conversation_slots",
        ["tenant_id", "conversation_id", "expires_at"],
    )
