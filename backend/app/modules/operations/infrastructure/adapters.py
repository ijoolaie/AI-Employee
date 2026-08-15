class InMemoryOperations:
    def __init__(self, services=None, metrics=None):
        self.services = services or []
        self._metrics = metrics or {}

    async def health_checks(self):
        return self.services

    async def metrics(self):
        return self._metrics
