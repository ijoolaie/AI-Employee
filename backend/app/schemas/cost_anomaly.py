from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CostAnomalyForecastResponse(BaseModel):
    as_of: datetime
    current_daily_cost_usd: float = Field(ge=0)
    baseline_daily_cost_usd: float = Field(ge=0)
    anomaly: bool
    anomaly_score: float
    month_to_date_cost_usd: float = Field(ge=0)
    projected_month_cost_usd: float = Field(ge=0)
    baseline_days: int = Field(ge=0)
    actions: list[str]
