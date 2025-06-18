@echo off
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "stop_servers.ps1"
pause