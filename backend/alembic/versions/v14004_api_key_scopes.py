"""Add explicit permission scopes to tenant API keys.

Revision ID: v14004apikeyscopes
Revises: rc9merge02
"""
from alembic import op
import sqlalchemy as sa

revision = "v14004apikeyscopes"
down_revision = "rc9merge02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NULL preserves the legacy behavior for keys created before V1.4-004.
    # Newly issued keys always persist an explicit scope list.
    op.add_column("api_keys", sa.Column("scopes", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("api_keys", "scopes")
