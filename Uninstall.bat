@echo off
rem Removes WaW Clone Wars. See README.md.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\uninstall.ps1"
pause
