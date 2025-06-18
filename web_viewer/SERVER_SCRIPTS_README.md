# ThermoAPI Web Viewer Server Scripts

This directory contains scripts to easily start and stop both the backend and frontend servers for the ThermoAPI Web Viewer.

## Files Created

### PowerShell Scripts
- `start_servers.ps1` - PowerShell script to start both servers
- `stop_servers.ps1` - PowerShell script to stop both servers

### Batch Files (Easy to Execute)
- `start_servers.bat` - Double-click to start both servers
- `stop_servers.bat` - Double-click to stop both servers

## How to Use

### Method 1: Double-click the .bat files
1. **To Start Servers**: Double-click `start_servers.bat`
2. **To Stop Servers**: Double-click `stop_servers.bat`

### Method 2: Run PowerShell scripts directly
1. Open PowerShell in this directory
2. Run `./start_servers.ps1` or `./stop_servers.ps1`

## What the Scripts Do

### Start Script (`start_servers.ps1`)
- Starts the Python backend server (`python main.py` in the backend directory)
- Waits 3 seconds for backend initialization
- Starts the React frontend server (`npm run dev` in the frontend directory)
- Shows server URLs:
  - Backend: http://localhost:5000
  - Frontend: http://localhost:3000 (or 3001 if 3000 is busy)

### Stop Script (`stop_servers.ps1`)
- Finds and terminates Python processes running from the backend directory
- Finds and terminates Node.js processes running from the frontend directory
- Also checks for processes running on ports 5000, 3000, and 3001
- Provides detailed feedback on what was stopped

## Converting to Executables

If you want to create actual .exe files, you can use these methods:

### Method 1: Using ps2exe (PowerShell to EXE)
1. Install ps2exe: `Install-Module ps2exe`
2. Convert scripts:
   ```powershell
   ps2exe -inputFile start_servers.ps1 -outputFile start_servers.exe
   ps2exe -inputFile stop_servers.ps1 -outputFile stop_servers.exe
   ```

### Method 2: Using Batch to EXE converters
- Use tools like "Bat To Exe Converter" to convert the .bat files
- This creates standalone executables that don't require PowerShell

### Method 3: Create shortcuts
1. Right-click on the .bat files
2. Select "Create shortcut"
3. Rename shortcuts to remove ".bat - Shortcut" suffix
4. Change icons if desired

## Prerequisites

- Python must be installed and accessible via `python` command
- Node.js and npm must be installed
- Backend dependencies must be installed (`pip install -r requirements.txt`)
- Frontend dependencies must be installed (`npm install`)

## Troubleshooting

- If scripts don't run, you may need to change PowerShell execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- If servers don't start, check that all dependencies are installed
- If ports are busy, the frontend will automatically try the next available port
- The stop script uses multiple methods to ensure all processes are terminated

## Security Note

The batch files use `-ExecutionPolicy Bypass` to run the PowerShell scripts. This is safe for these specific scripts but be cautious when running unknown PowerShell scripts with bypassed execution policies.