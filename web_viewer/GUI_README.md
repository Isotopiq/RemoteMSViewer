# ThermoAPI Server Manager GUI

A graphical user interface for managing the ThermoAPI Web Viewer backend and frontend servers with real-time status monitoring.

## Features

### 🖥️ User-Friendly Interface
- **Start/Stop Buttons**: Easy one-click server management
- **Real-time Status**: Live monitoring of server states
- **Server URLs**: Direct links to running servers
- **Activity Log**: Detailed logging of all operations

### 📊 Server Monitoring
- **Backend Status**: Monitors Python Flask server on port 5000
- **Frontend Status**: Monitors Vite dev server on ports 3000/3001
- **Health Checks**: Automatic port monitoring every 2 seconds
- **Process Tracking**: Tracks server processes for reliable shutdown

### 🔧 Smart Management
- **Automatic Port Detection**: Finds available ports for frontend
- **Graceful Shutdown**: Properly terminates all server processes
- **Error Handling**: Comprehensive error reporting and recovery
- **Directory Validation**: Checks for required backend/frontend folders

## Files Created

### Core Application
- `server_manager_gui.py` - Main GUI application
- `gui_requirements.txt` - Python dependencies
- `build_gui.bat` - Build script to create executable

### Build Output
- `ThermoAPI_Server_Manager.exe` - Compiled executable (after build)
- `dist/` - PyInstaller build directory
- `build/` - PyInstaller temporary files
- `ThermoAPI_Server_Manager.spec` - PyInstaller specification

## Quick Start

### Method 1: Run the Executable (Recommended)
1. **Build the executable** (one-time setup):
   ```bash
   double-click build_gui.bat
   ```
2. **Run the application**:
   ```bash
   double-click ThermoAPI_Server_Manager.exe
   ```

### Method 2: Run Python Script Directly
1. **Test dependencies**:
   ```bash
   python test_dependencies.py
   ```
2. **Test Node.js/npm**:
   ```bash
   python test_nodejs.py
   ```
3. **Test backend setup (if having issues)**:
   ```bash
   python test_backend.py
   ```
4. **Install missing dependencies**:
   ```bash
   pip install psutil requests
   ```
4. **Run the script**:
   ```bash
   python server_manager_gui.py
   ```

## Building the Executable

### Prerequisites
- Python 3.7+ installed
- pip package manager
- Internet connection (for downloading packages)

### Method 1: Using the PATH Fix Build Script (Recommended)
1. **Test dependencies first**:
   ```bash
   python test_dependencies.py
   ```
2. **Run the PATH fix build script**:
   ```bash
   build_gui_path_fix.bat
   ```
3. **Wait for completion** - The script will:
   - Check Python and tkinter availability
   - Install required packages using `python -m pip`
   - Test all imports
   - Build the executable using `python -m PyInstaller` (bypasses PATH issues)
   - Copy the result to the current directory

4. **Find your executable**: `ThermoAPI_Server_Manager.exe`

### Method 2: Using the Fixed Build Script
1. **Run the fixed build script**:
   ```bash
   build_gui_fixed.bat
   ```
   Note: May fail if PyInstaller is not in PATH.

### Method 3: Using the Original Build Script
1. **Run the build script**:
   ```bash
   build_gui.bat
   ```
   Note: This may fail if tkinter or PATH issues occur.

2. **What the build script does**:
   - Installs required Python packages
   - Uses PyInstaller to create a standalone executable
   - Copies the executable to the current directory
   - Creates a single-file executable with no external dependencies

3. **Build options used**:
   - `--onefile`: Creates a single executable file
   - `--windowed`: Runs without console window
   - `--name`: Sets executable name to "ThermoAPI_Server_Manager"

### Manual Build (Alternative)
If you prefer to build manually:
```bash
pip install -r gui_requirements.txt
pyinstaller --onefile --windowed --name "ThermoAPI_Server_Manager" server_manager_gui.py
copy dist\ThermoAPI_Server_Manager.exe .
```

## Using the GUI

### Main Interface
1. **Server Status Panel**:
   - Shows current status of backend and frontend servers
   - Displays server URLs when running
   - Updates automatically every 2 seconds

2. **Control Buttons**:
   - **Start Servers**: Launches both backend and frontend
   - **Stop Servers**: Terminates all server processes
   - **Refresh Status**: Manually updates server status

3. **Activity Log**:
   - Shows timestamped messages for all operations
   - Displays startup/shutdown progress
   - Reports errors and status changes
   - **Clear Log** button to reset the log

### Server Management

#### Starting Servers
1. Click **"Start Servers"** button
2. Backend starts first (Python Flask on port 5000)
3. Frontend starts after 3-second delay (Vite on port 3000/3001)
4. Status indicators turn green when servers are running
5. Server URLs appear next to status indicators

#### Stopping Servers
1. Click **"Stop Servers"** button
2. Application terminates tracked processes
3. Performs port-based cleanup for thorough shutdown
4. Status indicators turn red when servers are stopped

### Status Indicators
- **🔴 Red "Stopped"**: Server is not running
- **🟢 Green "Running"**: Server is active and responding
- **Blue URLs**: Click to open server in browser

## Technical Details

### Dependencies
- **tkinter**: GUI framework (built into Python)
- **psutil**: Process and system monitoring
- **requests**: HTTP client for health checks
- **subprocess**: Process management
- **threading**: Background monitoring
- **pathlib**: File system operations

### Architecture
- **Main Thread**: GUI updates and user interactions
- **Background Threads**: Server monitoring and process management
- **Process Tracking**: Maintains references to started processes
- **Port Monitoring**: Checks for active listeners on server ports

### Server Detection
- **Backend**: Monitors port 5000 for Flask server
- **Frontend**: Monitors ports 3000 and 3001 for Vite dev server
- **Health Checks**: Attempts HTTP requests to verify server response
- **Process Tracking**: Uses psutil to find processes by port binding

## Troubleshooting

### Build Issues
1. **"'pyinstaller' is not recognized as an internal or external command"**:
   - PyInstaller is installed but not in PATH
   - Use `build_gui_path_fix.bat` (uses `python -m PyInstaller`)
   - Or manually add `%APPDATA%\Python\Python313\Scripts` to your PATH
   - Alternative: Use `python -m PyInstaller` instead of `pyinstaller`

2. **"Could not find a version that satisfies the requirement tkinter"**:
   - tkinter is built into Python and doesn't need pip installation
   - Use `build_gui_fixed.bat` or `build_gui_path_fix.bat`
   - Run `python test_dependencies.py` to verify tkinter availability
   - If tkinter is missing, reinstall Python with tkinter support

3. **"Python not found"**: 
   - Ensure Python is installed and added to PATH
   - Download from https://python.org

4. **"Permission denied"**: 
   - Run as administrator
   - Check antivirus settings (may block PyInstaller)

### Runtime Issues
1. **"Module not found"**: 
   - Install missing dependencies: `pip install psutil requests`
   - Run dependency test: `python test_dependencies.py`

2. **"Failed to start frontend: npm not found"**:
   - Install Node.js from https://nodejs.org (includes npm)
   - Run `python test_nodejs.py` to verify installation
   - Ensure Node.js is added to your system PATH
   - Try restarting your computer after Node.js installation

3. **"Failed to start frontend: [WinError 2] The system cannot find the file specified"**:
   - This usually means npm is not found or not in PATH
   - Install Node.js from https://nodejs.org
   - Run `npm install` in the frontend directory
   - Use the updated GUI executable with better npm detection

### Backend Server Issues

1. **"Failed to start backend: [WinError 2] The system cannot find the file specified"**
   - Python is not installed or not in PATH
   - Solution: Install Python from python.org and ensure it's added to PATH
   - Alternative: Use `py` command instead of `python`

2. **"Backend server failed to start properly"**
   - Missing Python dependencies
   - Solution: Run `pip install -r backend/requirements.txt`
   - Check if all required packages are installed
   - **Use the "Test Backend" button in the GUI for detailed diagnostics**

3. **"Failed to start backend server with any Python command"**
   - Multiple Python installation issues
   - Missing required packages (flask, flask-socketio, flask-cors, pythonnet)
   - Solution: 
     - Run `python test_backend.py` for detailed diagnostics
     - Install missing packages: `pip install flask flask-socketio flask-cors pythonnet`
     - Try using `py` instead of `python`

4. **"Port 5000 already in use"**
   - Another application is using port 5000
   - Solution: Stop other applications or restart your computer

5. **Backend starts manually but fails from GUI**
   - Environment or PATH differences between manual and GUI execution
   - Solution: Use the "Test Backend" button to compare environments
   - Check if virtual environment is activated when running manually

4. **Servers won't start**: 
   - Check if ports 5000/3000/3001 are available
   - Ensure backend/frontend directories exist
   - Check if Python/Node.js are installed
   - Run dependency tests: `python test_dependencies.py` and `python test_nodejs.py`

5. **GUI doesn't respond**: 
   - Check if backend/frontend directories exist
   - Verify server scripts are in the correct location
   - Check Windows firewall settings

### GUI Issues
- **Window doesn't appear**: Check if running in background processes
- **Status not updating**: Click "Refresh Status" button
- **Log not scrolling**: Click in log area and scroll manually

## Advanced Usage

### Customization
Edit `server_manager_gui.py` to customize:
- Server ports and URLs
- Monitoring intervals
- GUI appearance and layout
- Logging behavior

### Integration
The executable can be:
- Added to Windows startup folder
- Pinned to taskbar or start menu
- Used in batch scripts or automation
- Deployed to other machines (no Python required)

### Deployment
The compiled executable:
- Requires no Python installation on target machine
- Includes all dependencies
- Can run from any directory
- Works on Windows 7, 8, 10, 11

## Security Notes

- The application manages local development servers only
- No network services are exposed beyond localhost
- Process termination uses standard Windows APIs
- No elevated privileges required for normal operation

## Support

For issues or questions:
1. Check the activity log for error messages
2. Verify backend and frontend directories exist
3. Ensure Python and Node.js are properly installed
4. Try running servers manually first to isolate issues