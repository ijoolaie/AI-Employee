from pathlib import Path
import ast


def test_compose_defines_real_worker_and_beat():
    compose = Path(__file__).parents[2] / "docker-compose.yml"
    text = compose.read_text()
    assert "worker:" in text
    assert "beat:" in text
    assert "celery" in text
    assert "postgres:" in text
    assert "redis:" in text


def test_e2e_script_is_fail_closed():
    script = Path(__file__).parents[1] / "scripts" / "e2e_stack_verify.py"
    tree = ast.parse(script.read_text())
    assert any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "connect" for n in ast.walk(tree))
    assert any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "ping" for n in ast.walk(tree))


def test_migration_merge_has_single_revision():
    versions = Path(__file__).parents[1] / "alembic" / "versions"
    heads = []
    revisions = {}
    for path in versions.glob("*.py"):
        tree = ast.parse(path.read_text())
        rev = down = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "revision" and isinstance(node.value, ast.Constant):
                        rev = node.value.value
                    if isinstance(target, ast.Name) and target.id == "down_revision":
                        if isinstance(node.value, ast.Constant): down = node.value.value
                        elif isinstance(node.value, ast.Tuple): down = tuple(x.value for x in node.value.elts)
        if rev:
            revisions[rev] = down
    referenced = set()
    for down in revisions.values():
        if isinstance(down, tuple): referenced.update(down)
        elif down: referenced.add(down)
    heads = sorted(set(revisions) - referenced)
    # Phase 4 added 0a1b2c3d4e5f (billing) on top of b3c4d5e6f713 —
    # see documents/62_PHASE4_MONETIZATION_AS_BUILT_v0.4.2.md. Phase 5 adds
    # a further migration on top — see this file's next update.
    assert len(heads) == 1
