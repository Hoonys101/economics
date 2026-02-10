@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

echo 🧹 Resetting Command Manifest to CLEAN template...
python _internal/scripts/launcher.py reset
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Reset failed.
    pause
    exit /b %ERRORLEVEL%
)
echo ✅ Manifest and Registry have been reset.
endlocal
