from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ModuleCommand:
    module: str
    name: str
    payload: dict[str, Any]
