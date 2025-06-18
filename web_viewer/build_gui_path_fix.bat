@echo off
echo Building ThermoAPI Server Manager GUI (PATH Fix Version)...
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
    pause
    exit /b 1
)

:: Install required packages individually
echo Installing required packages...
echo Installing psutil...
python -m pip install psutil>=5.9.0
if errorlevel 1 (
    echo Warning: Failed to install psutil
)

echo Installing requests...
python -m pip install requests>=2.28.0
if errorlevel 1 (
    echo Warning: Failed to install requests
)

echo Installing pyinstaller...
python -m pip install pyinstaller>=5.0.0
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
    echo   python -m pip install psutil requests
    pause
    exit /b 1
)

:: Clean up old build files first
echo Cleaning up old build files...
if exist "build" (
    rmdir /s /q "build" >nul 2>&1
)
if exist "dist" (
    rmdir /s /q "dist" >nul 2>&1
)
if exist "ThermoAPI_Server_Manager.spec" (
    del "ThermoAPI_Server_Manager.spec" >nul 2>&1
)

:: Build the executable using python -m pyinstaller (bypasses PATH issues)
echo.
echo Building GUI application with PATH fix and backend diagnostics...
python -m PyInstaller --onefile --windowed --name "ThermoAPI_Server_Manager" --icon=NONE server_manager_gui.py

if errorlevel 1 (
    echo Error: Failed to build executable using python -m PyInstaller
    echo.
    echo Troubleshooting steps:
    echo 1. Check if PyInstaller was installed correctly:
    echo    python -m pip show pyinstaller
    echo.
    echo 2. Try reinstalling PyInstaller:
    echo    python -m pip uninstall pyinstaller
    echo    python -m pip install pyinstaller
    echo.
    echo 3. Check for antivirus interference
    echo 4. Ensure sufficient disk space
    echo.
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
    echo IMPORTANT: This version includes fixes for:
    echo - npm/Node.js detection issues
    echo - psutil connection errors
    echo - Enhanced backend startup diagnostics
    echo - Better error reporting for backend failures
    echo.
    echo You can now:
    echo 1. Double-click ThermoAPI_Server_Manager.exe to run the GUI
    echo 2. Copy the .exe file to any Windows computer (no Python needed)
    echo 3. Create a desktop shortcut for easy access
    echo.
    echo To test your setup before running the GUI:
    echo   python test_nodejs.py     (test Node.js setup)
    echo   python test_backend.py    (test backend diagnostics)
    echo.
    echo Note: Make sure Node.js and npm are installed for frontend functionality
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