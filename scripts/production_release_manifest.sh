#!/usr/bin/env bash
set -euo pipefail

# Generate a release manifest without reading or printing secret values.
# Usage: bash scripts/production_release_manifest.sh [output-path]

OUTPUT="${1:-release-manifest.json}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SHA="$(git rev-parse HEAD)"
SHORT_SHA="$(git rev-parse --short HEAD)"
TAG="$(git describe --tags --exact-match HEAD 2>/dev/null || true)"
if [[ -z "$TAG" ]]; then TAG="unreleased-${SHORT_SHA}"; fi

python - "$OUTPUT" "$SHA" "$TAG" <<'PY'
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

output, sha, tag = sys.argv[1:]
root = Path.cwd()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

lockfiles = []
for candidate in (
    "backend/requirements.txt",
    "backend/requirements.lock",
    "frontend/package-lock.json",
    "frontend/pnpm-lock.yaml",
    "frontend/yarn.lock",
):
    p = root / candidate
    if p.is_file():
        lockfiles.append({"path": candidate, "sha256": digest(p)})

manifest = {
    "schema_version": 2,
    "release": {
        "git_sha": sha,
        "git_tree": git("rev-parse", f"{sha}^{{tree}}"),
        "git_tag": tag,
        "commit_timestamp_utc": git("show", "-s", "--format=%cI", sha),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dirty_worktree": bool(git("status", "--porcelain")),
    },
    "source": {"repository": "ijoolaie/AI-Employee"},
    "dependency_lock_identity": lockfiles,
    "build_identity": {
        "container_images": [],
        "sbom": None,
        "provenance": None,
        "external_release_status": "pending_external_build_pipeline",
    },
    "secret_values": "not included",
}
Path(output).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"release manifest written: {output}")
print(f"git sha: {sha}")
print(f"git tree: {manifest['release']['git_tree']}")
print(f"release identity: {tag}")
print("container/SBOM/provenance: pending external release pipeline")
PY
