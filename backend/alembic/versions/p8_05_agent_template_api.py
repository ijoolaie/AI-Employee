"""Stage 8 API permissions for governed AgentTemplate lifecycle.

Revision ID: p8_05_agent_template_api
Revises: p8_04_agent_governance
"""
from alembic import op
import sqlalchemy as sa

revision = "p8_05_agent_template_api"
down_revision = "p8_04_agent_governance"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("agent_template.create", "Create governed agent templates"),
    ("agent_template.read", "Read governed agent templates"),
    ("agent_template.publish", "Publish evaluated agent templates"),
    ("agent_template.install", "Provision governed agent instances from templates"),
)


def upgrade() -> None:
    for code, description in PERMISSIONS:
        op.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) "
                "VALUES (gen_random_uuid(), :code, :description) "
                "ON CONFLICT (code) DO NOTHING"
            ).bindparams(code=code, description=description)
        )


def downgrade() -> None:
    for code, _ in reversed(PERMISSIONS):
        op.execute(sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code=code))
