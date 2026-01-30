@echo off
setlocal
echo 🧹 Resetting Command Registry to CLEAN state...
python scripts/cmd_ops.py reset
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Reset failed.
    pause
    exit /b %ERRORLEVEL%
)
echo ✅ Registry has been reset.
endlocal
