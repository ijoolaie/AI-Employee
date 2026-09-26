"""Add dedicated RBAC permissions for Agent-to-Agent delegation lifecycle.

Revision ID: agentdelegationrbac
Revises: v1415agentdelegationrun
"""

from alembic import op
import sqlalchemy as sa

revision = "agentdelegationrbac"
down_revision = "v1415agentdelegationrun"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("agent_delegation.create", "Create governed Agent-to-Agent delegations"),
    ("agent_delegation.revoke", "Revoke governed Agent-to-Agent delegations"),
)


def upgrade() -> None:
    for code, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, description)
                VALUES (gen_random_uuid(), :code, :description)
                ON CONFLICT (code) DO NOTHING
                """
            ).bindparams(code=code, description=description)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r
                CROSS JOIN permissions p
                WHERE r.name = 'Admin'
                  AND p.code = :code
                  AND NOT EXISTS (
                      SELECT 1
                      FROM role_permissions rp
                      WHERE rp.role_id = r.id
                        AND rp.permission_id = p.id
                  )
                """
            ).bindparams(code=code)
        )


def downgrade() -> None:
    for code, _ in reversed(PERMISSIONS):
        op.execute(
            sa.text(
                """
                DELETE FROM role_permissions
                WHERE permission_id IN (
                    SELECT id FROM permissions WHERE code = :code
                )
                """
            ).bindparams(code=code)
        )
        op.execute(
            sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code=code)
        )
