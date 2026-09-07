"""Stage 8 governed AgentInstance lifecycle API permission.

Revision ID: p8_06_agent_instance_lifecycle
Revises: p8_05_agent_template_api
"""
from alembic import op
import sqlalchemy as sa

revision = "p8_06_agent_instance_lifecycle"
down_revision = "p8_05_agent_template_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) "
            "VALUES (gen_random_uuid(), 'agent_instance.lifecycle', 'Manage governed agent instance lifecycle') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'agent_instance.lifecycle'"))
