# ThermoAPI Web Viewer - Start Servers Script
# This script starts both the backend and frontend servers

Write-Host "Starting ThermoAPI Web Viewer Servers..." -ForegroundColor Green

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$frontendDir = Join-Path $scriptDir "frontend"

# Check if directories exist
if (-not (Test-Path $backendDir)) {
    Write-Host "Error: Backend directory not found at $backendDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $frontendDir)) {
    Write-Host "Error: Frontend directory not found at $frontendDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start backend server
Write-Host "Starting backend server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory $backendDir -WindowStyle Normal

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start frontend server
Write-Host "Starting frontend server..." -ForegroundColor Yellow
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $frontendDir -WindowStyle Normal

Write-Host "Both servers are starting up..." -ForegroundColor Green
Write-Host "Backend: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000 (or 3001 if 3000 is busy)" -ForegroundColor Cyan
Write-Host "" 
Write-Host "Use the stop_servers.ps1 script to stop both servers." -ForegroundColor Magenta
Write-Host "Press Enter to close this window..." -ForegroundColor Gray
Read-Host