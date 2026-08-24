#!/usr/bin/env python3
"""Audit the repository for common public-repository exposure risks.

The audit is intentionally conservative: findings that can be fixed automatically
are failures; questions requiring an owner/legal/security decision are reported as
REVIEW items instead of being silently marked safe.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
    re.compile(r"\bsk_live_[A-Za-z0-9]{12,}\b"),
)

PLACEHOLDER_MARKERS = {
    "REPLACE_WITH_SECRET_MANAGER_VALUE",
    "<GENERATE_STRONG_SECRET>",
    "<CUSTOMER_DOMAIN>",
    "ci-only-secret",
    "e2e-only-change-me",
    "sk_test_dummy_do_not_use",
    "whsec_test_only_do_not_use_in_prod",
}

FORBIDDEN_TRACKED_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.production.local",
}

REVIEW_BRANCH_PATTERNS = (
    re.compile(r"-temp$"),
    re.compile(r"-v\d+$"),
)


def run(*args: str, allow_failure: bool = False) -> bytes:
    """Run git commands without relying on the Windows console encoding."""
    result = subprocess.run(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=not allow_failure,
    )
    return result.stdout


def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def tracked_files() -> list[str]:
    return [p for p in decode(run("git", "ls-files")).splitlines() if p]


def tracked_content(path: str) -> str | None:
    result = subprocess.run(
        ("git", "show", f"HEAD:{path}"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return None
    return decode(result.stdout)


def current_tree_findings() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        name = Path(path).name
        if name in FORBIDDEN_TRACKED_NAMES:
            findings.append(f"tracked environment file: {path}")
        if Path(path).suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            findings.append(f"tracked private-key/certificate style file: {path}")
        content = tracked_content(path)
        if content is None:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(f"secret-like token in tracked file: {path} ({pattern.pattern})")
    return findings


def history_findings() -> list[str]:
    findings: list[str] = []
    # Inspect every reachable blob. This catches deleted secrets that are no
    # longer present in the current tree.
    object_lines = decode(run("git", "rev-list", "--objects", "--all")).splitlines()
    for line in object_lines:
        parts = line.split(" ", 1)
        sha = parts[0]
        path = parts[1] if len(parts) == 2 else "<no-path>"
        try:
            kind = decode(run("git", "cat-file", "-t", sha)).strip()
            if kind != "blob":
                continue
            size = int(decode(run("git", "cat-file", "-s", sha)).strip())
            if size > 2_000_000:
                continue
            content = decode(run("git", "cat-file", "blob", sha))
        except (subprocess.CalledProcessError, ValueError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(f"secret-like token in history blob {sha[:12]} ({path})")
    return sorted(set(findings))


def workflow_findings() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        if not path.startswith(".github/workflows/") or Path(path).suffix not in {".yml", ".yaml"}:
            continue
        content = tracked_content(path)
        if content is None:
            continue
        if re.search(r"(?m)^\s*permissions:\s*write-all\s*$", content):
            findings.append(f"workflow grants write-all permissions: {path}")
        if "pull_request_target" in content and re.search(r"actions/checkout@.*\n.*ref:.*github\.event\.pull_request\.head", content, re.S):
            findings.append(f"workflow checks out untrusted PR code under pull_request_target: {path}")
        if re.search(r"(?m)^\s*run:.*(printenv|env\s*$|cat\s+\.env)", content):
            findings.append(f"workflow may dump environment values: {path}")
    return findings


def branch_reviews() -> list[str]:
    reviews: list[str] = []
    try:
        refs = decode(
            run("git", "for-each-ref", "refs/remotes/origin", "--format=%(refname:short)")
        ).splitlines()
    except subprocess.CalledProcessError:
        return reviews
    for ref in refs:
        branch = ref.removeprefix("origin/")
        if branch in {"HEAD"}:
            continue
        if any(p.search(branch) for p in REVIEW_BRANCH_PATTERNS):
            reviews.append(f"review stale/temporary remote branch before publicization: {branch}")
    return sorted(reviews)


def main() -> int:
    failures = current_tree_findings() + history_findings() + workflow_findings()
    reviews = branch_reviews()

    for item in failures:
        print(f"PUBLIC_AUDIT|FAIL|{item}")
    for item in reviews:
        print(f"PUBLIC_AUDIT|REVIEW|{item}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    if ".env.*" not in gitignore or "!.env.example" not in gitignore:
        failures.append(".gitignore does not clearly exclude environment files while retaining .env.example")

    if not (ROOT / "SECURITY.md").exists():
        failures.append("SECURITY.md is missing")

    if failures:
        print(f"PUBLIC_AUDIT|SUMMARY|FAIL|{len(failures)} hard finding(s); {len(reviews)} review item(s)")
        return 1

    if not (ROOT / "LICENSE").exists():
        print("PUBLIC_AUDIT|REVIEW|LICENSE is absent; choose and add an explicit license before expecting contributors to reuse the code")
    print(f"PUBLIC_AUDIT|SUMMARY|PASS|0 hard finding(s); {len(reviews)} review item(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
