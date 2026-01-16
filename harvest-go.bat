@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Structured Command Registry (HITL 2.0)
:: This tool uses design/command_registry.json for its parameters.

python scripts/launcher.py harvest %*

endlocal
