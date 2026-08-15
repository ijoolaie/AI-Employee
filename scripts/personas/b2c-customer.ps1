param(
    [Parameter(Mandatory=$true)][string]$PublicChatUrl
)
$ErrorActionPreference = "Stop"
Write-Host "=== RC8 B2C Customer smoke path ==="
Write-Host "B2C customers do not create platform accounts."
Start-Process $PublicChatUrl
Write-Host "Verify: conversation creation -> customer message -> AI response -> conversation persistence."
Write-Host "B2C Customer path opened: PASS"
