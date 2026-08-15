"""Employee Framework — Employee (identity) + EmployeeVersion (content).

Per 11_Employee_Framework: an Employee is a first-class entity with a
name/identity that persists across versions; each meaningful change to
Prompt, Tools, or Schema creates a new EmployeeVersion. Runs lock to one
specific EmployeeVersion (never to "current"), so historical Runs stay
reproducible even after the Employee is edited (§4, §5 step 2).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Employee(Base):
    """The stable identity. tenant_id NULL = System Employee (11_Employee_Framework §6),
    available to tenants according to their plan; non-NULL = Custom Employee,
    scoped to that tenant only."""

    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_employee_tenant_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="system")
    # "system" | "custom"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    versions: Mapped[list["EmployeeVersion"]] = relationship(
        "EmployeeVersion", back_populates="employee", order_by="EmployeeVersion.version_number"
    )


class EmployeeVersion(Base):
    """One immutable, versioned definition of an Employee (11_Employee_Framework §4).

    Only one version per Employee may have is_current=True at a time; Runs
    always store the resolved employee_version_id, never "the current one",
    so Replay/Trace stay meaningful after future edits.
    """

    __tablename__ = "employee_versions"
    __table_args__ = (
        UniqueConstraint("employee_id", "version_number", name="uq_employee_version_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Definition per 11_Employee_Framework §3 / §8 (contract with AI Core)
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prompt_template: Mapped[str] = mapped_column(String, nullable=False, default="")
    allowed_tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="versions")
