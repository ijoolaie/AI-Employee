"""W18 governed tenant-scoped virtual meeting room domain."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="w18_virtual_meeting_rooms"; down_revision="w16_payout_reconcile"; branch_labels=None; depends_on=None

def upgrade():
    ms=postgresql.ENUM("scheduled","active","paused","ended","cancelled",name="meetingstatus",create_type=False)
    pr=postgresql.ENUM("host","participant","observer",name="meetingparticipantrole",create_type=False)
    ms.create(op.get_bind(),checkfirst=True); pr.create(op.get_bind(),checkfirst=True)
    op.create_table("meetings",
        sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("tenant_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("title",sa.String(255),nullable=False), sa.Column("description",sa.Text(),nullable=True),
        sa.Column("status",ms,nullable=False,server_default="scheduled"),
        sa.Column("created_by",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("work_item_id",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("run_id",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("scheduled_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("started_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("ended_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"],["users.id"],ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["work_item_id"],["work_items.id"],ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["run_id"],["runs.id"],ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_meetings_tenant_status","meetings",["tenant_id","status"]); op.create_index("ix_meetings_tenant_scheduled","meetings",["tenant_id","scheduled_at"]); op.create_index("ix_meetings_work_item_id","meetings",["work_item_id"]); op.create_index("ix_meetings_run_id","meetings",["run_id"])
    op.create_table("meeting_participants",
        sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("tenant_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("meeting_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("employee_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("role",pr,nullable=False,server_default="participant"),sa.Column("joined_at",sa.DateTime(timezone=True),nullable=True),sa.Column("left_at",sa.DateTime(timezone=True),nullable=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["meeting_id"],["meetings.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["employee_id"],["employees.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("tenant_id","meeting_id","employee_id",name="uq_meeting_participant"))
    op.create_index("ix_meeting_participants_tenant_meeting","meeting_participants",["tenant_id","meeting_id"])

def downgrade():
    op.drop_index("ix_meeting_participants_tenant_meeting",table_name="meeting_participants"); op.drop_table("meeting_participants")
    for n in ["ix_meetings_run_id","ix_meetings_work_item_id","ix_meetings_tenant_scheduled","ix_meetings_tenant_status"]: op.drop_index(n,table_name="meetings")
    op.drop_table("meetings"); sa.Enum(name="meetingparticipantrole").drop(op.get_bind(),checkfirst=True); sa.Enum(name="meetingstatus").drop(op.get_bind(),checkfirst=True)
