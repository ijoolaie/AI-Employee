"""W14 employee presentation profile.

Revision ID: w14_employee_presentation
Revises: w11_employee_avatar_identity
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w14_employee_presentation"
down_revision = "w11_employee_avatar_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "employees",
        sa.Column(
            "presentation_profile",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("employees", "presentation_profile", server_default=None)


def downgrade():
    op.drop_column("employees", "presentation_profile")
