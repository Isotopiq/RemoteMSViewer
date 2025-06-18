@echo off
echo Building ThermoAPI Server Manager GUI (Fixed Version)...
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Test tkinter availability
echo Checking tkinter availability...
python -c "import tkinter; print('tkinter is available')" >nul 2>&1
if errorlevel 1 (
    echo Error: tkinter is not available in your Python installation
    echo Please install Python with tkinter support or reinstall Python
    echo On some Linux systems, you may need: sudo apt-get install python3-tk
    pause
    exit /b 1
)

:: Install required packages individually
echo Installing psutil...
pip install psutil>=5.9.0
if errorlevel 1 (
    echo Warning: Failed to install psutil
)

echo Installing requests...
pip install requests>=2.28.0
if errorlevel 1 (
    echo Warning: Failed to install requests
)

echo Installing pyinstaller...
pip install pyinstaller>=5.0.0
if errorlevel 1 (
    echo Error: Failed to install pyinstaller
    echo PyInstaller is required to build the executable
    pause
    exit /b 1
)

:: Test imports
echo Testing required imports...
python -c "import tkinter, psutil, requests; print('All imports successful')"
if errorlevel 1 (
    echo Error: Some required packages are not available
    echo Please install missing packages manually:
    echo   pip install psutil requests
    pause
    exit /b 1
)

:: Build the executable
echo.
echo Building executable with PyInstaller...
:: Try using python -m pyinstaller first (recommended)
python -m pyinstaller --onefile --windowed --name "ThermoAPI_Server_Manager" --icon=NONE server_manager_gui.py

:: If that fails, try direct pyinstaller command
if errorlevel 1 (
    echo Python module approach failed, trying direct pyinstaller...
    pyinstaller --onefile --windowed --name "ThermoAPI_Server_Manager" --icon=NONE server_manager_gui.py
)

if errorlevel 1 (
    echo Error: Failed to build executable
    echo This could be due to:
    echo   1. Missing dependencies
    echo   2. Antivirus software blocking PyInstaller
    echo   3. Insufficient disk space
    echo   4. Python path issues
    pause
    exit /b 1
)

:: Copy executable to current directory
if exist "dist\ThermoAPI_Server_Manager.exe" (
    copy "dist\ThermoAPI_Server_Manager.exe" "ThermoAPI_Server_Manager.exe"
    echo.
    echo ========================================
    echo SUCCESS! Executable created successfully!
    echo ========================================
    echo.
    echo File: ThermoAPI_Server_Manager.exe
    echo Location: %CD%
    echo.
    echo You can now:
    echo 1. Double-click ThermoAPI_Server_Manager.exe to run the GUI
    echo 2. Copy the .exe file to any Windows computer (no Python needed)
    echo 3. Create a desktop shortcut for easy access
    echo.
) else (
    echo Error: Executable not found in dist folder
    echo Build may have failed silently
    if exist "dist" (
        echo Contents of dist folder:
        dir dist
    )
)

echo.
echo Build process complete.
echo Press any key to exit...
pause >nul