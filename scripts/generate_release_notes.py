#!/usr/bin/env python3
"""Generate release notes from the exact checked-out Git release reference."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def previous_release_tag(version: str) -> str | None:
    """Return the latest reachable release tag before ``version`` is created.

    During workflow_dispatch packaging, the requested version is normally not
    tagged yet. In that case ``git describe <version>^`` fails because the
    version ref does not exist. If the version tag already exists, resolving
    its parent preserves the expected behaviour for tag-triggered releases.
    """
    try:
        run("rev-parse", "--verify", f"refs/tags/{version}^{{commit}}")
    except subprocess.CalledProcessError:
        try:
            return run("describe", "--tags", "--abbrev=0", "HEAD")
        except subprocess.CalledProcessError:
            return None

    try:
        return run("describe", "--tags", "--abbrev=0", f"{version}^")
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: generate_release_notes.py <version>", file=sys.stderr)
        return 2

    version = sys.argv[1]
    if not version.startswith("v"):
        print("release version must start with v", file=sys.stderr)
        return 2

    commit = run("rev-parse", "HEAD")
    date = run("show", "-s", "--format=%cs", "HEAD")
    previous = previous_release_tag(version)

    range_spec = f"{previous}..HEAD" if previous else "HEAD"
    commits = run(
        "log",
        "--no-merges",
        "--pretty=format:- %s (%h)",
        range_spec,
    )
    files = (
        run("diff", "--name-only", previous, "HEAD")
        if previous
        else run("show", "--format=", "--name-only", "HEAD")
    )

    lines = [
        f"# Release Notes — {version}",
        "",
        f"- Release ref: `{version}`",
        f"- Exact source commit: `{commit}`",
        f"- Release date: `{date}`",
        f"- Previous release: `{previous}`" if previous else "- Previous release: none recorded",
        "",
        "## Changes",
        "",
        commits or "- No non-merge commits recorded in the selected range.",
        "",
        "## Changed Files",
        "",
    ]

    if files:
        lines.extend(f"- `{path}`" for path in files.splitlines() if path)
    else:
        lines.append("- No changed files reported.")

    lines.extend(
        [
            "",
            "## Integrity",
            "",
            "This document was generated from the exact Git revision checked out by the release workflow.",
            "It is informational only; package integrity is verified separately through `SHA256SUMS`.",
            "",
        ]
    )

    output = Path("dist/release/RELEASE_NOTES.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
