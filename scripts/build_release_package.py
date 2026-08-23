#!/usr/bin/env python3
"""Build a reproducible, secret-free AI Employee release package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = ROOT / "dist" / "release"

# Approved runtime/package inputs. Tests and local state are intentionally excluded.
INCLUDE_PATHS = (
    "backend/app",
    "backend/alembic",
    "backend/alembic.ini",
    "backend/Dockerfile",
    "backend/requirements.txt",
    "frontend",
    "delivery",
    "docker-compose.production.yml",
    "README.md",
    "CHANGELOG.md",
)

EXCLUDED_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "var",
    ".pytest_cache",
    ".ruff_cache",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
SECRET_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.production.local",
    ".env.test",
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_sha() -> str:
    return run("git", "rev-parse", "HEAD")


def git_tag_for_head() -> str | None:
    value = run("git", "tag", "--points-at", "HEAD")
    tags = [line for line in value.splitlines() if line.startswith("v")]
    return tags[0] if tags else None


def migration_head() -> str:
    """Resolve the authoritative Alembic head using the repository's Alembic CLI."""
    try:
        output = run("alembic", "-c", "backend/alembic.ini", "heads")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(
            "Unable to resolve Alembic head. Run from an environment with Alembic installed."
        ) from exc

    heads: list[str] = []
    for line in output.splitlines():
        token = line.strip().split()[0] if line.strip() else ""
        if token and all(ch.isalnum() or ch in "_-" for ch in token):
            heads.append(token)
    if len(heads) != 1:
        raise SystemExit(f"Expected exactly one Alembic head, found: {heads!r}")
    return heads[0]


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDED_NAMES for part in path.parts):
        return True
    if path.name in SECRET_FILENAMES or path.suffix in EXCLUDED_SUFFIXES:
        return True
    return False


def copy_path(source: Path, destination_root: Path) -> list[str]:
    copied: list[str] = []
    if source.is_file():
        if should_skip(source):
            raise SystemExit(f"Refusing to package excluded file: {source}")
        target = destination_root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return [str(source.relative_to(ROOT))]

    for path in source.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        target = destination_root / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(path.relative_to(ROOT)))
    return copied


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="release version, e.g. v1.1.1")
    parser.add_argument(
        "--certification-evidence",
        default="docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md",
    )
    args = parser.parse_args()

    if not args.version.startswith("v"):
        raise SystemExit("version must start with 'v'")

    sha = git_sha()
    tag = git_tag_for_head()
    if tag and tag != args.version:
        raise SystemExit(f"HEAD is tagged {tag}, not {args.version}")

    head = migration_head()
    work = DIST_ROOT / args.version
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    files: list[str] = []
    for relative in INCLUDE_PATHS:
        source = ROOT / relative
        if not source.exists():
            raise SystemExit(f"required package input is missing: {relative}")
        files.extend(copy_path(source, work))

    manifest = {
        "schema_version": 1,
        "product": "ai-employee",
        "release_version": args.version,
        "source_commit_sha": sha,
        "source_tag": tag or args.version,
        "migration_head": head,
        "certification_evidence": args.certification_evidence,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_policy": {
            "secrets_included": False,
            "runtime_source_allowlist": list(INCLUDE_PATHS),
            "excluded_local_state": sorted(EXCLUDED_NAMES),
        },
        "file_count": len(files),
        "files": sorted(files),
    }
    manifest_path = work / "RELEASE-MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = DIST_ROOT / f"ai-employee-{args.version}-runtime.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(work, arcname=f"ai-employee-{args.version}")

    checksum = sha256(archive)
    (DIST_ROOT / "SHA256SUMS").write_text(
        f"{checksum}  {archive.name}\n", encoding="utf-8"
    )
    print(f"release package: {archive}")
    print(f"sha256: {checksum}")
    print(f"migration head: {head}")


if __name__ == "__main__":
    main()
