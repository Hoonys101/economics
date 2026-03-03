@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Activate Virtual Environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: Structured Command Registry (HITL 2.0)
:: This tool uses _internal/registry/command_registry.json for its parameters.

python _internal/scripts/launcher.py harvest %*

endlocal
