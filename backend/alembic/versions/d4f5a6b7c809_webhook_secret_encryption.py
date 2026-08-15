"""Encrypted webhook secrets for newly created triggers.
Revision ID: d4f5a6b7c809
Revises: d3e4f5a6b708
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "d4f5a6b7c809"
down_revision = "d3e4f5a6b708"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("workflow_event_triggers", sa.Column("webhook_secret_encrypted", sa.String(1024), nullable=True))
    # Existing plaintext secrets are retained for backward compatibility and
    # are resolved by the application until rotated. Newly created triggers
    # never persist plaintext secrets.

def downgrade() -> None:
    op.drop_column("workflow_event_triggers", "webhook_secret_encrypted")
