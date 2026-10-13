@echo off
rem Starts World at War (Steam) with WaW Clone Wars on the zombie map you pick.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\play.ps1"
if errorlevel 1 pause
