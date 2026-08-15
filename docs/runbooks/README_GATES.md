# RC8 Certification Gate Runner

Run from the repository root in PowerShell:

```powershell
.\scripts\gates\doctor.ps1
.\scripts\gates\gate4-e2e.ps1
.\scripts\gates\gate5-security.ps1
.\scripts\gates\gate6-integrations.ps1
.\scripts\gates\gate7-dr.ps1
.\scripts\gates\gate8-performance.ps1
.\scripts\gates\gate9-final.ps1
```

These scripts are deliberately fail-closed: unavailable Docker, credentials, or staging services are reported as BLOCKED rather than converted into PASS.
