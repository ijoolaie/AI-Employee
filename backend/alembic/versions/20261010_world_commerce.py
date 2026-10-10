"""World Mode one-time commerce foundation.

Revision ID: 20261010_world_commerce
Revises: 20261007_outbox_tenant_dedupe
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261010_world_commerce"
down_revision = "20261007_outbox_tenant_dedupe"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("world.commerce.approve", "Review and approve World Mode manual payment submissions"),
    ("world.commerce.activate", "Activate approved World Mode purchases and entitlements"),
)


def upgrade() -> None:
    for code, description in PERMISSIONS:
        op.execute(sa.text("""
            INSERT INTO permissions (id, code, description)
            VALUES (gen_random_uuid(), :code, :description)
            ON CONFLICT (code) DO NOTHING
        """).bindparams(code=code, description=description))

    permission_codes = ", ".join(f"'{code}'" for code, _ in PERMISSIONS)
    op.execute(sa.text(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
          AND p.code IN ({permission_codes})
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """))
    op.create_table(
        "world_catalogue_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("item_type", sa.String(24), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_options", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_free", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("item_type IN ('room', 'layout', 'appearance', 'personality', 'furniture', 'facility', 'support')", name="ck_world_catalogue_item_type"),
    )
    op.create_index("ix_world_catalogue_items_is_active", "world_catalogue_items", ["is_active"])
    op.create_index("ix_world_catalogue_active_type", "world_catalogue_items", ["is_active", "item_type"])

    op.create_table(
        "world_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("buyer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("catalogue_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("world_catalogue_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_code_snapshot", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("payment_method", sa.String(32), nullable=False),
        sa.Column("payment_provider", sa.String(64), nullable=False),
        sa.Column("provider_transaction_ref", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending_payment"),
        sa.Column("payment_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by_username", sa.String(320), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("activated_by_username", sa.String(320), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("currency IN ('IRR', 'USD', 'USDT', 'WORLD_CREDIT')", name="ck_world_order_currency"),
        sa.CheckConstraint("status IN ('pending_payment', 'payment_submitted', 'approved', 'rejected', 'fulfilled', 'cancelled')", name="ck_world_order_status"),
        sa.CheckConstraint("amount >= 0", name="ck_world_order_amount_nonnegative"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_world_order_tenant_idempotency"),
    )
    op.create_index("ix_world_orders_tenant_id", "world_orders", ["tenant_id"])
    op.create_index("ix_world_orders_buyer_user_id", "world_orders", ["buyer_user_id"])
    op.create_index("ix_world_orders_catalogue_item_id", "world_orders", ["catalogue_item_id"])
    op.create_index("ix_world_orders_approved_by_user_id", "world_orders", ["approved_by_user_id"])
    op.create_index("ix_world_orders_activated_by_user_id", "world_orders", ["activated_by_user_id"])
    op.create_index("ix_world_orders_tenant_status_created", "world_orders", ["tenant_id", "status", "created_at"])
    op.create_index("ix_world_orders_status_created", "world_orders", ["status", "created_at"])

    op.create_table(
        "world_feature_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_code", sa.String(100), nullable=False),
        sa.Column("item_type", sa.String(24), nullable=False),
        sa.Column("source_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("world_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("activated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("activated_by_username", sa.String(320), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'revoked')", name="ck_world_entitlement_status"),
        sa.UniqueConstraint("tenant_id", "item_code", name="uq_world_entitlement_tenant_item"),
        sa.UniqueConstraint("source_order_id", name="uq_world_entitlement_source_order"),
    )
    op.create_index("ix_world_feature_entitlements_tenant_status", "world_feature_entitlements", ["tenant_id", "status"])

    op.create_table(
        "world_commerce_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("world_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_username", sa.String(320), nullable=True),
        sa.Column("from_status", sa.String(24), nullable=True),
        sa.Column("to_status", sa.String(24), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_world_commerce_events_tenant_created", "world_commerce_events", ["tenant_id", "created_at"])
    op.create_index("ix_world_commerce_events_order_created", "world_commerce_events", ["order_id", "created_at"])

    # Protect the event timeline from accidental or application-level mutation.
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_world_commerce_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'world_commerce_events is append-only';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_world_commerce_events_append_only
        BEFORE UPDATE OR DELETE ON world_commerce_events
        FOR EACH ROW EXECUTE FUNCTION prevent_world_commerce_event_mutation();
    """)


def downgrade() -> None:
    permission_codes = ", ".join(f"'{code}'" for code, _ in PERMISSIONS)
    op.execute(sa.text(f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions WHERE code IN ({permission_codes})
        )
    """))
    op.execute(sa.text(f"DELETE FROM permissions WHERE code IN ({permission_codes})"))
    op.execute("DROP TRIGGER IF EXISTS trg_world_commerce_events_append_only ON world_commerce_events")
    op.execute("DROP FUNCTION IF EXISTS prevent_world_commerce_event_mutation()")
    op.drop_table("world_commerce_events")
    op.drop_table("world_feature_entitlements")
    op.drop_table("world_orders")
    op.drop_table("world_catalogue_items")
