from pathlib import Path
import ast, json, sys

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"backend"/"app"
MODULES=APP/"modules"
contexts=["workflow","knowledge","crm","commerce","billing"]
errors=[]

for ctx in contexts:
    base=MODULES/ctx
    for layer in ["domain","application","infrastructure"]:
        if not (base/layer).is_dir():
            errors.append(f"missing layer: {ctx}/{layer}")

for owner in contexts:
    for p in (MODULES/owner).rglob("*.py"):
        try: tree=ast.parse(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"syntax: {p}: {e}"); continue
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom) and n.module:
                for target in set(contexts)-{owner}:
                    if n.module.startswith(f"app.modules.{target}."):
                        errors.append(f"cross-context import: {p} -> {n.module}")

if errors:
    print("\n".join(errors)); sys.exit(1)
print("M15 FINAL ARCHITECTURE AUDIT: PASS")
