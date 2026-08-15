$ErrorActionPreference='Stop'
Write-Host '=== Gate 7 — Backup / Restore / DR ==='
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Host 'BLOCKED: Docker unavailable; restore drill cannot be executed.'; exit 2 }
Write-Host 'Docker available. Execute the project DR runbook before certification.'
