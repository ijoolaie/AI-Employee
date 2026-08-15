$ErrorActionPreference = 'Continue'
Write-Host '=== RC8 Environment Doctor ==='
$checks = @(
  @{Name='Python'; Cmd='python --version'},
  @{Name='Node'; Cmd='node --version'},
  @{Name='NPM'; Cmd='npm --version'},
  @{Name='Docker'; Cmd='docker --version'},
  @{Name='Docker Compose'; Cmd='docker compose version'}
)
foreach ($c in $checks) {
  Write-Host "`n[$($c.Name)]"
  try { Invoke-Expression $c.Cmd } catch { Write-Host 'BLOCKED / unavailable' }
}
Write-Host "`nRequired environment: Docker daemon + PostgreSQL + Redis + Celery + frontend dependencies."
