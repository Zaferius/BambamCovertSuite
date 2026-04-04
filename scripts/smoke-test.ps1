$ErrorActionPreference = "Stop"

Write-Host "Checking API health..."
$health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
if ($health.status -ne "ok") {
    throw "API health check failed"
}

Write-Host "Checking jobs endpoint..."
$jobs = Invoke-RestMethod -Uri "http://localhost:8000/jobs" -Method Get
Write-Host "Jobs endpoint responded successfully"

Write-Host "Smoke test passed"
