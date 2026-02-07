@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: If arguments are provided, use classic launcher
if "%~1" neq "" (
    python _internal/scripts/launcher.py jules %*
) else (
    :: No arguments -> Interactive Mode
    python _internal/scripts/run_jules_interactive.py
)

endlocal
