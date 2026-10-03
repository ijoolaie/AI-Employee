"""Add stable Employee avatar presentation metadata for Workforce identity."""
from alembic import op
import sqlalchemy as sa

revision = "w11_employee_avatar_identity"
down_revision = "v1415agentdelegationrun"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employees", "avatar_url")
