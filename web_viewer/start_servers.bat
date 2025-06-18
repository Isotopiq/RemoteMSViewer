@echo off
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "start_servers.ps1"
pause