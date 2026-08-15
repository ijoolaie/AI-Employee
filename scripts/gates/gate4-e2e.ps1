$ErrorActionPreference='Stop'
Write-Host '=== Gate 4 — Full E2E ==='
python -m compileall -q backend/app
Push-Location frontend
node scripts/test-frontend-contract.mjs
Pop-Location
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Host 'BLOCKED: Docker CLI/daemon unavailable'; exit 2 }
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose ps
