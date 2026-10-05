"""Governed tenant-scoped virtual meeting session domain for W18."""
from __future__ import annotations
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class MeetingStatus(str, enum.Enum):
    SCHEDULED="scheduled"; ACTIVE="active"; PAUSED="paused"; ENDED="ended"; CANCELLED="cancelled"

class MeetingParticipantRole(str, enum.Enum):
    HOST="host"; PARTICIPANT="participant"; OBSERVER="observer"

class Meeting(Base):
    __tablename__="meetings"
    __table_args__=(Index("ix_meetings_tenant_status","tenant_id","status"),Index("ix_meetings_tenant_scheduled","tenant_id","scheduled_at"))
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False)
    title: Mapped[str]=mapped_column(String(255),nullable=False)
    description: Mapped[str|None]=mapped_column(Text,nullable=True)
    status: Mapped[MeetingStatus]=mapped_column(Enum(MeetingStatus,values_callable=lambda e:[x.value for x in e]),nullable=False,default=MeetingStatus.SCHEDULED)
    created_by: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    work_item_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("work_items.id",ondelete="SET NULL"),nullable=True,index=True)
    run_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("runs.id",ondelete="SET NULL"),nullable=True,index=True)
    scheduled_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    ended_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)

class MeetingParticipant(Base):
    __tablename__="meeting_participants"
    __table_args__=(UniqueConstraint("tenant_id","meeting_id","employee_id",name="uq_meeting_participant"),Index("ix_meeting_participants_tenant_meeting","tenant_id","meeting_id"))
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False)
    meeting_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("meetings.id",ondelete="CASCADE"),nullable=False)
    employee_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("employees.id",ondelete="CASCADE"),nullable=False)
    role: Mapped[MeetingParticipantRole]=mapped_column(Enum(MeetingParticipantRole,values_callable=lambda e:[x.value for x in e]),nullable=False,default=MeetingParticipantRole.PARTICIPANT)
    joined_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    left_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
