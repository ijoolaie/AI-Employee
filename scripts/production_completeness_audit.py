from pathlib import Path
import ast, sys, json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend"
required_docs = [
    ROOT/"docs/production/SECURITY_HARDENING.md",
    ROOT/"docs/production/BACKUP_DISASTER_RECOVERY.md",
    ROOT/"docs/production/BILLING_ENTITLEMENTS.md",
    ROOT/"docs/production/ACCESSIBILITY.md",
    ROOT/"docs/production/DEVELOPER_PORTAL.md",
]
errors = []

for p in required_docs:
    if not p.exists():
        errors.append(f"missing production contract: {p}")

for p in APP.rglob("*.py"):
    try:
        ast.parse(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"python syntax error: {p}: {e}")

if FRONTEND.exists():
    for p in [FRONTEND/"playwright.config.ts", FRONTEND/"e2e/critical-flows.spec.ts"]:
        if not p.exists():
            errors.append(f"missing frontend E2E file: {p}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("PRODUCTION COMPLETENESS BASELINE: PASS")
