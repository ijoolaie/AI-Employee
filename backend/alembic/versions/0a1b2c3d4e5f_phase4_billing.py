"""Phase 4 monetization: plans, subscriptions and idempotent billing events.
Revision ID: 0a1b2c3d4e5f
Revises: d3e4f5a6b708
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0a1b2c3d4e5f"; down_revision=("d3e4f5a6b708", "b3c4d5e6f713"); branch_labels=None; depends_on=None

def upgrade():
    op.create_table("billing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("monthly_price_usd", sa.Numeric(12,2), nullable=False, server_default="0"),
        sa.Column("monthly_runs", sa.Integer(), nullable=False, server_default="100"), sa.Column("monthly_tokens", sa.Integer(), nullable=False, server_default="100000"),
        sa.Column("max_employees", sa.Integer(), nullable=False, server_default="3"), sa.Column("max_workflows", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_billing_plans_code","billing_plans",["code"],unique=True); op.create_index("ix_billing_plans_is_active","billing_plans",["is_active"])
    op.create_table("subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("billing_plans.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("provider", sa.String(40), nullable=False, server_default="manual"), sa.Column("provider_customer_id", sa.String(255)), sa.Column("provider_subscription_id", sa.String(255), unique=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False), sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False), sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("canceled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_unique_constraint("uq_subscription_tenant","subscriptions",["tenant_id"]); op.create_index("ix_subscription_status","subscriptions",["status"])
    op.create_table("billing_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL")),
        sa.Column("provider", sa.String(40), nullable=False), sa.Column("provider_event_id", sa.String(255), nullable=False), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("status", sa.String(20), nullable=False, server_default="processed"), sa.Column("error", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_unique_constraint("uq_billing_event_provider_id","billing_events",["provider","provider_event_id"]); op.create_index("ix_billing_event_tenant","billing_events",["tenant_id"])

def downgrade():
    op.drop_index("ix_billing_event_tenant", table_name="billing_events"); op.drop_constraint("uq_billing_event_provider_id","billing_events",type_="unique"); op.drop_table("billing_events")
    op.drop_index("ix_subscription_status", table_name="subscriptions"); op.drop_constraint("uq_subscription_tenant","subscriptions",type_="unique"); op.drop_table("subscriptions")
    op.drop_index("ix_billing_plans_is_active", table_name="billing_plans"); op.drop_index("ix_billing_plans_code", table_name="billing_plans"); op.drop_table("billing_plans")
