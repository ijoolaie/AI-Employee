$ErrorActionPreference = "Stop"

Write-Host "=== AI Employee Platform 1.0.0-rc.7 production certification ==="

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker not found." }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python not found." }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm not found." }

Write-Host "`n[1/5] Infrastructure"
Push-Location backend
docker compose up -d postgres redis
docker compose ps

Write-Host "`n[2/5] Python compile"
if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" -m compileall -q app
} else {
    python -m compileall -q app
}

Write-Host "`n[3/5] Alembic"
if (Test-Path ".venv\Scripts\alembic.exe") {
    & ".venv\Scripts\alembic.exe" upgrade head
    & ".venv\Scripts\alembic.exe" current
    & ".venv\Scripts\alembic.exe" heads
    & ".venv\Scripts\alembic.exe" check
} else {
    alembic upgrade head
    alembic current
    alembic heads
    alembic check
}
Pop-Location

Write-Host "`n[4/5] Backend tests"
Push-Location backend
if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" -m pytest tests -v --tb=short
} else {
    python -m pytest tests -v --tb=short
}
Pop-Location

Write-Host "`n[5/5] Frontend"
Push-Location frontend
npm install
npm run test
npm run test:unit
npm run build
Pop-Location

Write-Host "`n=== Verification finished ==="
