from __future__ import annotations
from app.modules.operations.domain.models import ServiceHealth, SystemSnapshot

class OperationsApplicationService:
    def __init__(self, health_checks, metrics):
        self.health_checks = health_checks
        self.metrics = metrics

    async def snapshot(self) -> SystemSnapshot:
        services = tuple(await self.health_checks())
        metrics = await self.metrics()
        return SystemSnapshot(
            services=services,
            queue_depth=metrics.get("queue_depth", 0),
            error_rate=metrics.get("error_rate", 0.0),
            active_tenants=metrics.get("active_tenants", 0),
        )
