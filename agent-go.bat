@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Antigravity Agent Interface
:: Reads context from design/agent_context.json and launches Interactive CLI

python _internal/scripts/agent_interface.py

endlocal
