@echo off
rem Builds WaW Clone Wars from your own World at War + Star Wars Battlefront II files and installs it. See README.md.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" %*
pause
