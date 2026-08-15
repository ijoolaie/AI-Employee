from __future__ import annotations
from typing import Any

class LegacyEmbeddingProvider:
    """Adapter for the existing embedding/vector provider."""
    def __init__(self, provider: Any) -> None:
        self.provider = provider

    async def embed(self, texts: list[str]) -> list[list[float]]:
        result = await self.provider.embed(texts)
        return result if isinstance(result, list) else []
