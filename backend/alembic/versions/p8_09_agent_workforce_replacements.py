"""Add governed AgentInstance replacement lineage to workforce proposals.

Revision ID: p809agentwfreplace
Revises: p0eimmutableaudit, f1a2b3c4d5e6
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p809agentwfreplace"
down_revision = ("p0eimmutableaudit", "f1a2b3c4d5e6")
branch_labels = None
depends_on = None

PERMISSION = ("agent_workforce.replace", "Manage governed AgentInstance replacement cutovers")


def upgrade() -> None:
    proposal_kind = postgresql.ENUM(
        "staffing",
        "replacement",
        name="agentworkforceproposalkind",
        create_type=False,
    )
    proposal_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "agent_workforce_proposals",
        sa.Column(
            "kind",
            proposal_kind,
            nullable=False,
            server_default="staffing",
        ),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column(
            "replacement_for_agent_instance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column("replacement_cutover_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column("replacement_retired_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_workforce_proposals_tenant_replacement",
        "agent_workforce_proposals",
        ["tenant_id", "replacement_for_agent_instance_id"],
    )
    op.alter_column("agent_workforce_proposals", "kind", server_default=None)

    code, description = PERMISSION
    op.execute(sa.text(
        "INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), :code, :description) "
        "ON CONFLICT (code) DO NOTHING"
    ).bindparams(code=code, description=description))
    op.execute(sa.text(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
        "WHERE r.name = 'Admin' AND p.code = :code "
        "ON CONFLICT DO NOTHING"
    ).bindparams(code=code))


def downgrade() -> None:
    code, _ = PERMISSION
    op.execute(sa.text(
        "DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code = :code)"
    ).bindparams(code=code))
    op.execute(sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code=code))
    op.drop_index(
        "ix_agent_workforce_proposals_tenant_replacement",
        table_name="agent_workforce_proposals",
    )
    op.drop_column("agent_workforce_proposals", "replacement_retired_at")
    op.drop_column("agent_workforce_proposals", "replacement_cutover_at")
    op.drop_column("agent_workforce_proposals", "replacement_for_agent_instance_id")
    op.drop_column("agent_workforce_proposals", "kind")
    sa.Enum(name="agentworkforceproposalkind").drop(op.get_bind(), checkfirst=True)
