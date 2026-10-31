"""Allow product inventory to represent an unknown provider quantity.

Manual product creation continues to default inventory to zero. Shopify sync
stores NULL only when the provider omits or returns a null quantity.
"""
from alembic import op
import sqlalchemy as sa

revision = "w27_product_inventory_nullable"
down_revision = "w26_customer_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("products", "inventory", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Downgrade cannot preserve unknown separately; make the lossy conversion explicit.
    op.execute("UPDATE products SET inventory = 0 WHERE inventory IS NULL")
    op.alter_column("products", "inventory", existing_type=sa.Integer(), nullable=False)
