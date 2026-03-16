@echo off
chcp 65001 >nul
echo Updating External PFC...
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Download latest from GitHub
curl -sL https://raw.githubusercontent.com/Avichay1977/external-pfc/main/pfc_windows.py -o pfc_windows.py.new
if errorlevel 1 (
    echo Update failed - no internet or repo not found.
    pause
    exit /b 1
)

:: Compare and replace if different
fc /b pfc_windows.py pfc_windows.py.new >nul 2>&1
if errorlevel 1 (
    move /y pfc_windows.py.new pfc_windows.py >nul
    echo Updated! Restarting PFC...
    taskkill /F /IM pythonw.exe >nul 2>&1
    wscript "%SCRIPT_DIR%launch_pfc.vbs"
    echo Done.
) else (
    del pfc_windows.py.new
    echo Already up to date.
)
pause
