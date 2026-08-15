$ErrorActionPreference='Stop'
Write-Host '=== Gate 8 — Performance / Load ==='
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Host 'BLOCKED: Docker unavailable; load test cannot be executed.'; exit 2 }
Write-Host 'Infrastructure available. Load-test tooling and thresholds must be executed against staging.'
