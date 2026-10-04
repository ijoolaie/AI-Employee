from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SkillInstallationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    skill_package_id: UUID
    status: str
    installed_at: datetime
    revoked_at: datetime | None = None
