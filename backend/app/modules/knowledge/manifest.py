from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleManifest:
    slug: str = "knowledge"
    name: str = "Knowledge, RAG & Memory"
    version: str = "1.0"
    capabilities: tuple[str, ...] = ('knowledge', 'memory', 'rag')

MANIFEST = ModuleManifest()
