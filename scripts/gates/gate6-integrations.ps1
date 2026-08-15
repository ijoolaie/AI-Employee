$ErrorActionPreference='Stop'
Write-Host '=== Gate 6 — Billing & External Integrations ==='
Push-Location frontend
node scripts/test-frontend-contract.mjs
Pop-Location
Write-Host 'Static/contract surface PASS.'
Write-Host 'Live Stripe/Shopify/WhatsApp/email/webhook certification requires staging credentials.'
