$ErrorActionPreference='Stop'
Write-Host '=== Gate 5 — Security & Compliance Static Gate ==='
$patterns='sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|DEBUG\s*=\s*True|verify=False|ssl_verify=False'
$hits = Get-ChildItem backend,frontend -Recurse -File | Select-String -Pattern $patterns -ErrorAction SilentlyContinue
if ($hits) { $hits | ForEach-Object { $_.Line }; exit 1 }
Write-Host 'PASS: no known secret/debug/unsafe-TLS patterns found.'
Write-Host 'Dynamic security certification still requires a running staging stack.'
