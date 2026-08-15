from pathlib import Path
import ast

APP = Path(__file__).parents[1] / "app"
MODULES = APP / "modules"
CONTEXTS = {"workflow", "knowledge", "crm", "commerce", "billing"}

def imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (x.name for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""

def test_cross_module_contracts_exist():
    assert (MODULES / "contracts" / "events.py").exists()
    assert (APP / "shared" / "commands.py").exists()
    assert (APP / "shared" / "queries.py").exists()

def test_contexts_do_not_import_each_other():
    for owner in CONTEXTS:
        for path in (MODULES / owner).rglob("*.py"):
            for imp in imports(path):
                for target in CONTEXTS - {owner}:
                    assert not imp.startswith(f"app.modules.{target}."), (
                        f"{path} imports {imp}; use contracts/events instead"
                    )

def test_event_wiring_exists():
    assert (APP / "infrastructure" / "event_wiring.py").exists()
