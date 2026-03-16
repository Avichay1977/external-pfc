@echo off
chcp 65001 >nul
echo ============================================
echo   External PFC - Windows Installer
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Download: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH"!
    pause
    exit /b 1
)

echo [1/3] Installing Python packages...
pip install "mediapipe==0.10.14" opencv-python "numpy<2" --quiet

echo [2/3] Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
set SCRIPT_DIR=%~dp0

:: Create VBS launcher
> "%SCRIPT_DIR%launch_pfc.vbs" echo Set WshShell = CreateObject("WScript.Shell")
>> "%SCRIPT_DIR%launch_pfc.vbs" echo WshShell.Run "pythonw """ ^& Replace(WScript.ScriptFullName, "launch_pfc.vbs", "pfc_windows.py") ^& """", 0, False

:: Desktop shortcut
> "%TEMP%\mk_shortcut.vbs" echo Set s = WScript.CreateObject("WScript.Shell").CreateShortcut("%DESKTOP%\PFC Monitor.lnk")
>> "%TEMP%\mk_shortcut.vbs" echo s.TargetPath = "wscript.exe"
>> "%TEMP%\mk_shortcut.vbs" echo s.Arguments = """%SCRIPT_DIR%launch_pfc.vbs"""
>> "%TEMP%\mk_shortcut.vbs" echo s.WorkingDirectory = "%SCRIPT_DIR%"
>> "%TEMP%\mk_shortcut.vbs" echo s.Description = "External PFC Monitor"
>> "%TEMP%\mk_shortcut.vbs" echo s.Save
cscript //nologo "%TEMP%\mk_shortcut.vbs"
del "%TEMP%\mk_shortcut.vbs"

echo [3/3] Setting auto-start with Windows...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy "%SCRIPT_DIR%launch_pfc.vbs" "%STARTUP%\PFC Monitor.vbs" >nul

echo.
echo ============================================
echo   Done!
echo   - Desktop shortcut created
echo   - Auto-starts with Windows
echo   - Log saved to: %SCRIPT_DIR%pfc_log.csv
echo ============================================
pause
