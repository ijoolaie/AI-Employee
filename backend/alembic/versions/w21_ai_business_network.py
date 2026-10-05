"""W21 governed AI Business Network request envelope."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="w21_ai_business_network"; down_revision="w20_employee_marketplace"; branch_labels=None; depends_on=None
def upgrade():
    status_enum=postgresql.ENUM("pending_approval","approved","rejected","cancelled",name="businessnetworkrequeststatus",create_type=False); status_enum.create(op.get_bind(),checkfirst=True)
    op.create_table("business_network_requests",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("sender_tenant_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("recipient_tenant_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("requester_user_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("sponsor_user_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("operation",sa.String(100),nullable=False),
        sa.Column("capability_contract",postgresql.JSONB(),nullable=False),
        sa.Column("payload",postgresql.JSONB(),nullable=False),
        sa.Column("idempotency_key",sa.String(200),nullable=False),
        sa.Column("correlation_id",sa.String(200),nullable=False),
        sa.Column("status",status_enum,nullable=False),
        sa.Column("decision_by",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("decision_reason",sa.Text(),nullable=True),
        sa.Column("decided_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.ForeignKeyConstraint(["sender_tenant_id"],["tenants.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recipient_tenant_id"],["tenants.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_user_id"],["users.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sponsor_user_id"],["users.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["decision_by"],["users.id"],ondelete="RESTRICT"),
        sa.UniqueConstraint("sender_tenant_id","idempotency_key",name="uq_business_network_sender_idempotency"))
    op.create_index("ix_business_network_requests_sender_status","business_network_requests",["sender_tenant_id","status"])
    op.create_index("ix_business_network_requests_recipient_status","business_network_requests",["recipient_tenant_id","status"])
    op.create_index("ix_business_network_requests_correlation_id","business_network_requests",["correlation_id"])
    op.execute(sa.text("INSERT INTO permissions (id,code,description) VALUES (gen_random_uuid(),'business_network.submit','Submit a governed cross-company business network request'),(gen_random_uuid(),'business_network.decide','Approve or reject a governed cross-company business network request') ON CONFLICT (code) DO NOTHING"))
    op.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT r.id,p.id FROM roles r CROSS JOIN permissions p WHERE r.name='Admin' AND p.code IN ('business_network.submit','business_network.decide') ON CONFLICT DO NOTHING"))
def downgrade():
    op.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ('business_network.submit','business_network.decide'))"))
    op.execute(sa.text("DELETE FROM permissions WHERE code IN ('business_network.submit','business_network.decide')"))
    op.drop_index("ix_business_network_requests_correlation_id",table_name="business_network_requests"); op.drop_index("ix_business_network_requests_recipient_status",table_name="business_network_requests"); op.drop_index("ix_business_network_requests_sender_status",table_name="business_network_requests"); op.drop_table("business_network_requests"); postgresql.ENUM(name="businessnetworkrequeststatus").drop(op.get_bind(),checkfirst=True)
