from __future__ import annotations
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend" / "src"
POLICY = ROOT / "architecture" / "module-boundaries.json"

policy = json.loads(POLICY.read_text(encoding="utf-8"))
contexts = set(policy["backend_contexts"])
errors: list[str] = []

def imports(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        errors.append(f"Syntax error in {path}: {exc}")
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module

# Backend bounded contexts may not import each other directly.
modules = BACKEND / "modules"
for owner in contexts:
    owner_dir = modules / owner
    if not owner_dir.exists():
        errors.append(f"Missing backend context: {owner}")
        continue
    for path in owner_dir.rglob("*.py"):
        for imp in imports(path) or ():
            for target in contexts - {owner}:
                if imp.startswith(f"app.modules.{target}."):
                    errors.append(
                        f"Forbidden cross-context import: {path} -> {imp}"
                    )

# Employee modules may not import bounded-context implementations directly.
employees = modules / "employees"
if employees.exists():
    for path in employees.rglob("*.py"):
        for imp in imports(path) or ():
            for target in contexts:
                if imp.startswith(f"app.modules.{target}."):
                    errors.append(
                        f"Forbidden employee->context import: {path} -> {imp}"
                    )

# No application module may import infrastructure adapters directly.
for path in modules.rglob("*.py"):
    for imp in imports(path) or ():
        if imp.startswith("app.infrastructure.adapters."):
            errors.append(
                f"Forbidden infrastructure adapter import: {path} -> {imp}"
            )

# Frontend must not reference backend Python modules or infrastructure.
if FRONTEND.exists():
    for path in FRONTEND.rglob("*"):
        if path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            forbidden = ("app.infrastructure", "backend/app", "sqlalchemy", "stripe", "shopify")
            for token in forbidden:
                if token in text:
                    errors.append(f"Forbidden frontend dependency: {path} contains {token}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("Architecture check passed.")
