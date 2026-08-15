"""Security hardening: webhook secret rotation timestamp.
Revision ID: a1b2c3d4e507
Revises: f5a6b7c8d901
"""
from alembic import op
import sqlalchemy as sa
revision = "a1b2c3d4e507"
down_revision = "f5a6b7c8d901"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("workflow_event_triggers", sa.Column("secret_rotated_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("workflow_event_triggers", "secret_rotated_at")
