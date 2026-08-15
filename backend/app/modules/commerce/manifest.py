from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleManifest:
    slug: str = "commerce"
    name: str = "Commerce & Orders"
    version: str = "1.0"
    capabilities: tuple[str, ...] = ('orders', 'products', 'shopify')

MANIFEST = ModuleManifest()
