param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [string]$TenantName = "Demo Tenant",
    [string]$TenantSlug = "demo",
    [string]$Email = "admin@demo.com",
    [string]$Password = "Admin123!",
    [string]$FullName = "Demo Tenant Admin",
    [switch]$Register
)
$ErrorActionPreference = "Stop"
Write-Host "=== RC8 Tenant Admin smoke path ==="
$health = Invoke-RestMethod "$ApiUrl/health"
if ($health.status -ne "ok") { throw "API health check failed." }
if ($Register) {
    $body = @{ tenant_name=$TenantName; tenant_slug=$TenantSlug; email=$Email; password=$Password; full_name=$FullName } | ConvertTo-Json
    try { Invoke-RestMethod -Method Post -Uri "$ApiUrl/api/v1/auth/register" -ContentType "application/json" -Body $body | Out-Null; Write-Host "Registration: PASS" }
    catch { Write-Warning "Registration failed or tenant already exists: $($_.Exception.Message)" }
}
$loginBody = @{ email=$Email; password=$Password; tenant_slug=$TenantSlug } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$ApiUrl/api/v1/auth/login" -ContentType "application/json" -Body $loginBody
$token = $login.data.access_token
if (-not $token) { throw "Login succeeded without an access token." }
$headers = @{ Authorization = "Bearer $token" }
$me = Invoke-RestMethod -Uri "$ApiUrl/api/v1/auth/me" -Headers $headers
Write-Host "Authenticated: $($me.data.email)"
Write-Host "Tenant: $($me.data.tenant_slug)"
Write-Host "Dashboard: $FrontendUrl/dashboard"
Write-Host "Tenant Admin smoke path: PASS"
