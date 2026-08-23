#!/usr/bin/env python3
"""Build a reproducible, secret-free AI Employee runtime release package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = ROOT / "dist" / "release"

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
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".next",
    "dist", "var", ".pytest_cache", ".ruff_cache",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
SECRET_FILENAMES = {".env", ".env.local", ".env.production", ".env.production.local", ".env.test"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bsk-proj-[A-Za-z0-9_-]{20,}\b"),
)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_sha() -> str:
    return run("git", "rev-parse", "HEAD")


def git_commit_time() -> str:
    return run("git", "show", "-s", "--format=%cI", "HEAD")


def git_tag_for_head() -> str | None:
    value = run("git", "tag", "--points-at", "HEAD")
    tags = [line for line in value.splitlines() if line.startswith("v")]
    return tags[0] if tags else None


def migration_head() -> str:
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
    return (
        any(part in EXCLUDED_NAMES for part in path.parts)
        or path.name in SECRET_FILENAMES
        or path.suffix in EXCLUDED_SUFFIXES
    )


def copy_path(source: Path, destination_root: Path) -> list[str]:
    copied: list[str] = []
    if source.is_file():
        if should_skip(source):
            raise SystemExit(f"Refusing to package excluded file: {source}")
        target = destination_root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return [str(source.relative_to(ROOT))]

    for path in sorted(source.rglob("*")):
        if not path.is_file() or should_skip(path):
            continue
        target = destination_root / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(path.relative_to(ROOT)))
    return copied


def scan_for_secrets(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "RELEASE-MANIFEST.json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise SystemExit(f"possible secret material found in package input: {path}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    # Normalize metadata so the same commit produces the same archive bytes.
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


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

    scan_for_secrets(work)
    files = sorted(files)
    manifest = {
        "schema_version": 1,
        "product": "ai-employee",
        "release_version": args.version,
        "source_commit_sha": sha,
        "source_tag": tag or args.version,
        "source_commit_time": git_commit_time(),
        "migration_head": head,
        "certification_evidence": args.certification_evidence,
        "artifact_policy": {
            "secrets_included": False,
            "runtime_source_allowlist": list(INCLUDE_PATHS),
            "excluded_local_state": sorted(EXCLUDED_NAMES),
        },
        "file_count": len(files),
        "files": files,
    }
    manifest_path = work / "RELEASE-MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = DIST_ROOT / f"ai-employee-{args.version}-runtime.tar.gz"
    if archive.exists():
        archive.unlink()
    with tarfile.open(archive, "w:gz", compresslevel=9) as tar:
        for path in sorted(work.rglob("*")):
            tar.add(path, arcname=f"ai-employee-{args.version}/{path.relative_to(work)}", recursive=False, filter=tar_filter)

    checksum = sha256(archive)
    (DIST_ROOT / "SHA256SUMS").write_text(
        f"{checksum}  {archive.name}\n", encoding="utf-8"
    )
    print(f"release package: {archive}")
    print(f"sha256: {checksum}")
    print(f"migration head: {head}")


if __name__ == "__main__":
    main()
