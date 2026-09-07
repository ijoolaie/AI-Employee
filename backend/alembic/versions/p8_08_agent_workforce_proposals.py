"""Persist dynamic Agent workforce governance proposals.

Revision ID: p8_08_agent_workforce
Revises: p8_07_gov_merge
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_08_agent_workforce"
down_revision = "p8_07_gov_merge"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("agent_workforce.propose", "Submit governed Agent workforce proposals"),
    ("agent_workforce.read", "Read governed Agent workforce proposals"),
    ("agent_workforce.board_review", "Review Agent workforce proposals as the Board authority"),
    ("agent_workforce.ceo_approve", "Approve Agent workforce proposals as the CEO authority"),
    ("agent_workforce.provision", "Provision CEO-approved Agent workforce proposals"),
    ("agent_workforce.activate", "Activate Agent workforce after approved access review"),
)


def upgrade() -> None:
    proposal_status = postgresql.ENUM(
        "submitted", "board_approved", "board_rejected", "ceo_approved",
        "ceo_rejected", "provisioned", "cancelled",
        name="agentworkforceproposalstatus",
        create_type=False,
    )
    proposal_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "agent_workforce_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_templates.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("requested_name", sa.String(length=255), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sponsor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("risk_tier", sa.Integer(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column("status", proposal_status, nullable=False),
        sa.Column("board_reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("board_decision_reason", sa.Text(), nullable=True),
        sa.Column("ceo_approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ceo_decision_reason", sa.Text(), nullable=True),
        sa.Column("provisioned_agent_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_workforce_proposals_tenant_status", "agent_workforce_proposals", ["tenant_id", "status"])
    op.create_index("ix_agent_workforce_proposals_tenant_template", "agent_workforce_proposals", ["tenant_id", "agent_template_id"])

    for code, description in PERMISSIONS:
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
    for code, _ in reversed(PERMISSIONS):
        op.execute(sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code = :code)"
        ).bindparams(code=code))
        op.execute(sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code=code))
    op.drop_index("ix_agent_workforce_proposals_tenant_template", table_name="agent_workforce_proposals")
    op.drop_index("ix_agent_workforce_proposals_tenant_status", table_name="agent_workforce_proposals")
    op.drop_table("agent_workforce_proposals")
    sa.Enum(name="agentworkforceproposalstatus").drop(op.get_bind(), checkfirst=True)
