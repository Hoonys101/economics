@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Structured Command Registry (HITL 2.0)
:: This tool runs independently of the json registry.
:: Usage: git-go.bat <branch_name> [instruction]

python scripts/launcher.py git-review %*

endlocal
