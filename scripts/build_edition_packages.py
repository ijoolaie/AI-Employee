#!/usr/bin/env python3
"""Build Vendor, Reseller and Customer delivery packages from one source tree.

The builder deliberately keeps one runtime source and varies only the delivery
profile/manifest. It never packages local secrets and every profile records the
same vendor release identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist" / "editions"
INCLUDE_PATHS = (
    "backend/app",
    "backend/alembic",
    "backend/alembic.ini",
    "backend/Dockerfile",
    "backend/requirements.txt",
    "frontend",
    "docker-compose.production.yml",
)
PROFILES = ("vendor", "reseller", "customer")
SECRET_NAMES = {".env", ".env.local", ".env.production", ".env.production.local"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_tree(relative: str, destination: Path) -> list[str]:
    source = ROOT / relative
    if not source.exists():
        raise SystemExit(f"missing required source path: {relative}")
    copied: list[str] = []
    if source.is_file():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return [relative]
    for path in sorted(source.rglob("*")):
        if not path.is_file() or any(part in {".git", "dist", "__pycache__", "node_modules", ".next"} for part in path.parts):
            continue
        if path.name in SECRET_NAMES or path.suffix in {".pyc", ".pyo"}:
            continue
        target = destination / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(path.relative_to(ROOT)))
    return copied


def _profile_manifest(
    edition: str,
    *,
    release_tag: str,
    commit_sha: str,
    revision: str,
    reseller_id: str,
    customer_id: str,
) -> dict:
    base = {
        "schema_version": 1,
        "edition": edition,
        "vendor": {
            "product": "AI-Employee",
            "release_tag": release_tag,
            "commit_sha": commit_sha,
        },
        "profile": {
            "name": edition,
            "revision": revision,
            "release_channel": edition,
        },
        "deployment": {
            "environment": "production",
            "image_policy": "immutable-digest",
        },
        "secrets": {"policy": "external-secret-store", "included": False},
    }
    if edition == "vendor":
        base["reseller"] = None
        base["customer"] = None
        base["authority"] = "product"
    elif edition == "reseller":
        base["reseller"] = {"id": reseller_id, "delivery_revision": revision}
        base["customer"] = None
        base["authority"] = "delegated"
    else:
        base["reseller"] = {"id": reseller_id if reseller_id else None, "delivery_revision": "external-or-null"}
        base["customer"] = {"id": customer_id, "deployment_revision": revision}
        base["authority"] = "consumed"
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_tag")
    parser.add_argument("commit_sha")
    parser.add_argument("--vendor-revision", default="1")
    parser.add_argument("--reseller-revision", default="1")
    parser.add_argument("--customer-revision", default="1")
    parser.add_argument("--reseller-id", default="RESELLER-EXAMPLE-001")
    parser.add_argument("--customer-id", default="CUSTOMER-EXAMPLE-001")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    if not args.release_tag.startswith("v"):
        raise SystemExit("release_tag must start with v")
    if len(args.commit_sha) != 40 or any(ch not in "0123456789abcdef" for ch in args.commit_sha.lower()):
        raise SystemExit("commit_sha must be a 40-character hexadecimal SHA")

    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    revisions = {
        "vendor": args.vendor_revision,
        "reseller": args.reseller_revision,
        "customer": args.customer_revision,
    }
    artifacts: list[dict] = []

    for edition in PROFILES:
        profile_root = out / edition
        profile_root.mkdir(parents=True)
        files: list[str] = []
        for relative in INCLUDE_PATHS:
            files.extend(_copy_tree(relative, profile_root))

        (profile_root / "delivery" / "profile").mkdir(parents=True, exist_ok=True)
        profile = json.loads((ROOT / "delivery" / "profiles" / edition / "profile.json").read_text(encoding="utf-8"))
        (profile_root / "delivery" / "profile" / "PROFILE.json").write_text(
            json.dumps(profile, indent=2) + "\n", encoding="utf-8"
        )
        manifest = _profile_manifest(
            edition,
            release_tag=args.release_tag,
            commit_sha=args.commit_sha,
            revision=revisions[edition],
            reseller_id=args.reseller_id,
            customer_id=args.customer_id,
        )
        (profile_root / "delivery" / "profile" / "EDITION-MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        archive = out / f"ai-employee-{args.release_tag}-{edition}.{revisions[edition]}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for path in sorted(profile_root.rglob("*")):
                if path.is_file():
                    tar.add(path, arcname=f"ai-employee-{args.release_tag}-{edition}.{revisions[edition]}/{path.relative_to(profile_root)}")
        artifacts.append({
            "edition": edition,
            "revision": revisions[edition],
            "artifact": archive.name,
            "sha256": _sha256(archive),
            "source_commit_sha": args.commit_sha,
        })

    (out / "EDITION-RELEASE-MANIFEST.json").write_text(
        json.dumps({
            "schema_version": 1,
            "vendor_release_tag": args.release_tag,
            "vendor_commit_sha": args.commit_sha,
            "artifacts": artifacts,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifacts, indent=2))


if __name__ == "__main__":
    main()
