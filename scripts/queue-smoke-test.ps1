$ErrorActionPreference = "Stop"

Write-Host "Checking API health..."
$health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
if ($health.status -ne "ok") {
    throw "API health check failed"
}

Write-Host "Checking jobs endpoint..."
$jobs = Invoke-RestMethod -Uri "http://localhost:8000/jobs" -Method Get

Write-Host "Checking cleanup endpoint..."
$cleanup = Invoke-RestMethod -Uri "http://localhost:8000/admin/cleanup?older_than_hours=24" -Method Post

Write-Host "Queue-backed smoke test passed"
