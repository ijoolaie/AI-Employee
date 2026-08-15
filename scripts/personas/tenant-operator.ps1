param(
    [string]$ApiUrl = "http://localhost:8000",
    [Parameter(Mandatory=$true)][string]$TenantSlug,
    [Parameter(Mandatory=$true)][string]$Email,
    [Parameter(Mandatory=$true)][string]$Password
)
$ErrorActionPreference = "Stop"
Write-Host "=== RC8 Tenant Operator smoke path ==="
$loginBody = @{ email=$Email; password=$Password; tenant_slug=$TenantSlug } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$ApiUrl/api/v1/auth/login" -ContentType "application/json" -Body $loginBody
$token = $login.data.access_token
if (-not $token) { throw "Login succeeded without an access token." }
$headers = @{ Authorization = "Bearer $token" }
$me = Invoke-RestMethod -Uri "$ApiUrl/api/v1/auth/me" -Headers $headers
Write-Host "Authenticated: $($me.data.email)"
Write-Host "Tenant: $($me.data.tenant_slug)"
Write-Host "Operator role is not auto-granted. Configure tenant RBAC explicitly."
Write-Host "Tenant Operator authentication path: PASS"
