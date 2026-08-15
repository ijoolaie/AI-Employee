$ErrorActionPreference = "Stop"

# Resolve the project root from this script location so the script can be
# launched from any working directory.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== AI Employee Platform 1.0.0-rc.8 bootstrap ==="
Write-Host "Project root: $ProjectRoot"

Set-Location $ProjectRoot

# Basic tool checks
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11 and enable the Python launcher."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js LTS and restart PowerShell."
}

# Frontend toolchain requires Node 22.13+.
$NodeVersion = (& node --version).TrimStart("v")
try {
    $Node = [version]$NodeVersion
} catch {
    throw "Could not parse Node.js version: $NodeVersion"
}
if ($Node -lt [version]"22.13.0") {
    throw "Node.js 22.13.0 or newer is required. Current version: $NodeVersion"
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install/start Docker Desktop and restart PowerShell."
}

$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

# Environment files
$BackendEnv = Join-Path $BackendDir ".env"
$BackendEnvExample = Join-Path $BackendDir ".env.example"
if (-not (Test-Path $BackendEnv)) {
    if (-not (Test-Path $BackendEnvExample)) {
        throw "Missing backend\.env.example at $BackendEnvExample"
    }
    Copy-Item $BackendEnvExample $BackendEnv
    Write-Host "Created backend\.env from template. Set SECRET_KEY before non-local use."
}

$FrontendEnv = Join-Path $FrontendDir ".env.local"
$FrontendEnvExample = Join-Path $FrontendDir ".env.example"
if (-not (Test-Path $FrontendEnv)) {
    if (-not (Test-Path $FrontendEnvExample)) {
        throw "Missing frontend\.env.example at $FrontendEnvExample"
    }
    Copy-Item $FrontendEnvExample $FrontendEnv
    Write-Host "Created frontend\.env.local from template."
}

# Backend virtual environment and dependencies
Set-Location $BackendDir

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python 3.11 virtual environment..."
    & py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment."
    }
}

$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
$Alembic = Join-Path $BackendDir ".venv\Scripts\alembic.exe"

Write-Host "Upgrading pip..."
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

Write-Host "Installing backend requirements..."
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed." }

Write-Host "Starting PostgreSQL and Redis..."
& docker compose up -d postgres redis
if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed to start PostgreSQL/Redis." }

Write-Host "Applying Alembic migrations..."
& $Alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed." }

Write-Host "Checking Alembic state..."
& $Alembic current
& $Alembic heads
& $Alembic check
if ($LASTEXITCODE -ne 0) { throw "Alembic check failed." }

# Frontend dependencies
Set-Location $FrontendDir
Write-Host "Installing frontend dependencies..."
& npm install
if ($LASTEXITCODE -ne 0) { throw "Frontend npm install failed." }

Set-Location $ProjectRoot

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Next: read docs/current/02_WINDOWS_RUNBOOK.md"
Write-Host "API:      cd backend  ; .\.venv\Scripts\Activate.ps1 ; uvicorn app.main:app --reload --port 8000"
Write-Host "Celery:   cd backend  ; .\.venv\Scripts\Activate.ps1 ; python -m celery -A app.workers.celery_app worker -l info --pool=solo"
Write-Host "Frontend: cd frontend ; npm run dev"
