@echo off
echo Building ThermoAPI Server Manager GUI...
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Install required packages
echo Installing required packages...
echo Note: tkinter is built into Python and does not need separate installation
pip install -r gui_requirements.txt

if errorlevel 1 (
    echo Error: Failed to install requirements
    echo Please check your internet connection and Python installation
    pause
    exit /b 1
)

:: Build the executable
echo.
echo Building executable with PyInstaller...
pyinstaller --onefile --windowed --name "ThermoAPI_Server_Manager" --icon=NONE server_manager_gui.py

if errorlevel 1 (
    echo Error: Failed to build executable
    pause
    exit /b 1
)

:: Copy executable to current directory
if exist "dist\ThermoAPI_Server_Manager.exe" (
    copy "dist\ThermoAPI_Server_Manager.exe" "ThermoAPI_Server_Manager.exe"
    echo.
    echo Success! Executable created: ThermoAPI_Server_Manager.exe
    echo.
    echo You can now run the GUI by double-clicking ThermoAPI_Server_Manager.exe
) else (
    echo Error: Executable not found in dist folder
)

echo.
echo Build process complete.
pause