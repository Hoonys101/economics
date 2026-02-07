@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Structured Command Registry (HITL 2.0)
:: This tool uses _internal/registry/command_registry.json for its parameters.

python _internal/scripts/launcher.py harvest %*

endlocal
