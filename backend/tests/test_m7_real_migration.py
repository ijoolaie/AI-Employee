from pathlib import Path
import ast

APP = Path(__file__).parents[1] / "app"
MODULES = APP / "modules"
CONTEXTS = {"workflow", "knowledge", "crm", "commerce", "billing"}

def test_context_layers_exist():
    for name in CONTEXTS:
        base = MODULES / name
        for layer in ("domain", "application", "infrastructure"):
            assert (base / layer).is_dir()
            assert (base / layer / "__init__.py").exists()

def test_shared_application_service_exists():
    assert (APP / "shared" / "application_service.py").exists()

def test_no_new_direct_cross_context_imports():
    for owner in CONTEXTS:
        for path in (MODULES / owner).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for target in CONTEXTS - {owner}:
                        assert not node.module.startswith(f"app.modules.{target}.")
