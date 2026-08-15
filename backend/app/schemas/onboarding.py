from typing import Any
from pydantic import BaseModel, Field

class OnboardingUpdate(BaseModel):
    step: int = Field(ge=1, le=6)
    business_type: str | None = Field(default=None, max_length=80)
    data: dict[str, Any] = Field(default_factory=dict)
    complete_step: bool = True

class OnboardingResponse(BaseModel):
    current_step: int
    completed_steps: list[int]
    business_type: str | None
    setup_data: dict[str, Any]
    completed: bool
