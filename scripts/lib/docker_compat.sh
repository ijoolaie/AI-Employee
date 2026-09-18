#!/usr/bin/env bash
set -euo pipefail

# Resolve Docker without hard-coding a developer-specific installation path.
# Native Linux/macOS: docker from PATH.
# Windows/WSL or Git Bash: prefer docker.exe when docker is unavailable.
if command -v docker >/dev/null 2>&1 && docker --version >/dev/null 2>&1; then
  DOCKER_CMD=(docker)
elif command -v docker.exe >/dev/null 2>&1 && docker.exe --version >/dev/null 2>&1; then
  DOCKER_CMD=(docker.exe)
elif command -v cmd.exe >/dev/null 2>&1 && cmd.exe /c docker --version >/dev/null 2>&1; then
  DOCKER_CMD=(cmd.exe /c docker)
else
  echo "Docker runtime not found. Install Docker Desktop/Docker Engine or make it available on PATH." >&2
  exit 1
fi

docker_cmd() {
  "${DOCKER_CMD[@]}" "$@"
}

docker_compose() {
  docker_cmd compose "$@"
}
