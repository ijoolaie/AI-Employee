param(
    [Parameter(Mandatory=$true)][string]$TenantSlug,
    [Parameter(Mandatory=$true)][string]$Email,
    [string]$BackendDir = "$PSScriptRoot\..\..\backend",
    [string]$ApiUrl = "http://localhost:8000"
)
$ErrorActionPreference = "Stop"
Write-Host "=== RC8 Platform Admin provisioning path ==="
Set-Location (Resolve-Path $BackendDir)
$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Backend virtualenv missing. Run .\scripts\bootstrap.ps1 first." }
& $python scripts/promote_platform_admin.py --tenant-slug $TenantSlug --email $Email
if ($LASTEXITCODE -ne 0) { throw "Platform admin promotion failed." }
Write-Host "Platform admin flag granted explicitly to $Email."
Write-Host "After login, open $ApiUrl/docs and frontend /admin."
Write-Host "Platform Admin provisioning path: PASS"
