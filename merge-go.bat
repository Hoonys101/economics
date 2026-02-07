@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Structured Command Registry (HITL 2.0)
:: This tool runs independently of the json registry.
:: Usage: merge-go.bat <branch_name>

python _internal/scripts/launcher.py merge %*

endlocal
