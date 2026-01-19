@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Structured Command Registry (HITL 2.0)
:: Usage: jules-go.bat [command] [args...]

python scripts/launcher.py jules %*

endlocal
