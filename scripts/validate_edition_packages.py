#!/usr/bin/env python3
"""Validate generated Vendor, Reseller and Customer edition packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

EXPECTED = {"vendor", "reseller", "customer"}
SECRET_NAMES = {".env", ".env.local", ".env.production", ".env.production.local"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_archive(path: Path, *, edition: str, release_tag: str, commit_sha: str) -> None:
    if not path.exists():
        raise SystemExit(f"missing artifact: {path}")
    with tarfile.open(path, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        if not members:
            raise SystemExit(f"empty artifact: {path}")
        names = {Path(m.name).name for m in members}
        if SECRET_NAMES & names:
            raise SystemExit(f"{edition}: secret file included in artifact: {sorted(SECRET_NAMES & names)}")
        manifest_members = [m for m in members if m.name.endswith("/delivery/profile/EDITION-MANIFEST.json")]
        profile_members = [m for m in members if m.name.endswith("/delivery/profile/PROFILE.json")]
        if len(manifest_members) != 1 or len(profile_members) != 1:
            raise SystemExit(f"{edition}: expected exactly one edition manifest and profile")
        manifest = json.load(tar.extractfile(manifest_members[0]))
        profile = json.load(tar.extractfile(profile_members[0]))

    if manifest.get("edition") != edition:
        raise SystemExit(f"{edition}: embedded manifest edition mismatch")
    if manifest.get("vendor", {}).get("release_tag") != release_tag:
        raise SystemExit(f"{edition}: release tag mismatch")
    if manifest.get("vendor", {}).get("commit_sha") != commit_sha:
        raise SystemExit(f"{edition}: source commit mismatch")
    if manifest.get("secrets", {}).get("included") is True:
        raise SystemExit(f"{edition}: manifest claims included secrets")
    if profile.get("edition") != edition:
        raise SystemExit(f"{edition}: embedded profile mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "EDITION-RELEASE-MANIFEST.json"
    if not manifest_path.exists():
        raise SystemExit(f"missing edition release manifest: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise SystemExit("unsupported edition release manifest schema")
    release_tag = data.get("vendor_release_tag")
    commit_sha = data.get("vendor_commit_sha")
    artifacts = data.get("artifacts")
    if not isinstance(release_tag, str) or not release_tag.startswith("v"):
        raise SystemExit("invalid vendor release tag")
    if not isinstance(commit_sha, str) or len(commit_sha) != 40 or any(c not in "0123456789abcdef" for c in commit_sha.lower()):
        raise SystemExit("invalid vendor commit SHA")
    if not isinstance(artifacts, list) or {item.get("edition") for item in artifacts} != EXPECTED:
        raise SystemExit("edition manifest must contain exactly vendor, reseller and customer artifacts")

    for item in artifacts:
        edition = item["edition"]
        artifact = item["artifact"]
        path = root / edition / artifact
        if item.get("path") != f"{edition}/{artifact}":
            raise SystemExit(f"{edition}: manifest path mismatch")
        if item.get("source_commit_sha") != commit_sha:
            raise SystemExit(f"{edition}: artifact source commit mismatch")
        digest = _sha256(path)
        if digest != item.get("sha256"):
            raise SystemExit(f"{edition}: checksum mismatch")
        _validate_archive(path, edition=edition, release_tag=release_tag, commit_sha=commit_sha)

    print("phase6 edition packages valid")
    print(f"vendor_release_tag={release_tag}")
    print(f"vendor_commit_sha={commit_sha}")
    print("artifacts=vendor,reseller,customer")


if __name__ == "__main__":
    main()
