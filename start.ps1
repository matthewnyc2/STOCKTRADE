param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

# Kill existing processes on the ports
Write-Host "Checking for existing processes on ports $BackendPort and $FrontendPort..."

$backendProcesses = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if ($backendProcesses) {
    Write-Host "Killing processes on port $BackendPort..."
    foreach ($conn in $backendProcesses) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$frontendProcesses = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
if ($frontendProcesses) {
    Write-Host "Killing processes on port $FrontendPort..."
    foreach ($conn in $frontendProcesses) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 1

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Start backend in background
Write-Host "Starting backend on port $BackendPort..."
$backendJob = Start-Job -ScriptBlock {
    param($port)
    Set-Location $args[0]
    & .\venv\Scripts\Activate.ps1
    uvicorn api.main:app --host 0.0.0.0 --port $port --reload
} -ArgumentList @($BackendPort, (Get-Location))

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in background
Write-Host "Starting frontend on port $FrontendPort..."
$frontendJob = Start-Job -ScriptBlock {
    param($port)
    Set-Location $args[0]
    cd frontend
    npm run dev -- -p $port
} -ArgumentList @($FrontendPort, (Get-Location))

Write-Host "`n✓ Both services are starting..."
Write-Host "  Backend: http://localhost:$BackendPort"
Write-Host "  Backend Docs: http://localhost:$BackendPort/docs"
Write-Host "  Frontend: http://localhost:$FrontendPort"
Write-Host "`nPress Ctrl+C to stop all services"

# Keep script running and monitor jobs
while ($true) {
    if ((Get-Job -Id $backendJob.Id).State -eq "Failed") {
        Write-Host "Backend job failed!" -ForegroundColor Red
        Receive-Job -Id $backendJob.Id
    }
    if ((Get-Job -Id $frontendJob.Id).State -eq "Failed") {
        Write-Host "Frontend job failed!" -ForegroundColor Red
        Receive-Job -Id $frontendJob.Id
    }
    Start-Sleep -Seconds 2
}
