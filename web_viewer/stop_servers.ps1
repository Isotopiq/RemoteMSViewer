# ThermoAPI Web Viewer - Stop Servers Script
# This script stops both the backend and frontend servers

Write-Host "Stopping ThermoAPI Web Viewer Servers..." -ForegroundColor Red

# Function to kill processes by name and working directory
function Stop-ServerProcesses {
    param(
        [string]$ProcessName,
        [string]$WorkingDirectory,
        [string]$ServerType
    )
    
    $processes = Get-WmiObject Win32_Process | Where-Object { 
        $_.Name -eq $ProcessName -and 
        $_.CommandLine -like "*$WorkingDirectory*"
    }
    
    if ($processes) {
        foreach ($process in $processes) {
            try {
                Stop-Process -Id $process.ProcessId -Force
                Write-Host "Stopped $ServerType server (PID: $($process.ProcessId))" -ForegroundColor Yellow
            }
            catch {
                Write-Host "Failed to stop $ServerType server (PID: $($process.ProcessId)): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "No $ServerType server processes found" -ForegroundColor Gray
    }
}

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$frontendDir = Join-Path $scriptDir "frontend"

# Stop Python processes (backend)
Write-Host "Stopping backend server..." -ForegroundColor Yellow
Stop-ServerProcesses -ProcessName "python.exe" -WorkingDirectory $backendDir -ServerType "backend"

# Stop Node.js processes (frontend)
Write-Host "Stopping frontend server..." -ForegroundColor Yellow
Stop-ServerProcesses -ProcessName "node.exe" -WorkingDirectory $frontendDir -ServerType "frontend"

# Also try to stop any npm processes
Get-Process -Name "npm" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force
        Write-Host "Stopped npm process (PID: $($_.Id))" -ForegroundColor Yellow
    }
    catch {
        Write-Host "Failed to stop npm process (PID: $($_.Id)): $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Alternative method: Kill processes by port (if the above doesn't work)
Write-Host "Checking for processes on ports 5000 and 3000-3001..." -ForegroundColor Gray

$ports = @(5000, 3000, 3001)
foreach ($port in $ports) {
    try {
        $connections = netstat -ano | Select-String ":$port "
        if ($connections) {
            foreach ($connection in $connections) {
                $parts = $connection.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)
                if ($parts.Length -ge 5) {
                    $pid = $parts[-1]
                    if ($pid -match '^\d+$') {
                        try {
                            Stop-Process -Id $pid -Force
                            Write-Host "Stopped process on port $port (PID: $pid)" -ForegroundColor Yellow
                        }
                        catch {
                            Write-Host "Failed to stop process on port $port (PID: $pid): $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }
                }
            }
        }
    }
    catch {
        Write-Host "Error checking port $port : $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Server shutdown complete." -ForegroundColor Green
Write-Host "Press Enter to close this window..." -ForegroundColor Gray
Read-Host