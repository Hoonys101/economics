@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: If arguments are provided, use classic launcher
if "%~1" neq "" (
    python scripts/launcher.py gemini %*
) else (
    :: No arguments -> Interactive Mode
    python scripts/run_gemini_interactive.py
)

endlocal
