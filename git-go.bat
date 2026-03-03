@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Activate Virtual Environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: Structured Command Registry (HITL 2.0)
:: This tool runs independently of the json registry.
:: Usage: git-go.bat <branch_name> [instruction]

python _internal/scripts/launcher.py git-review %*

endlocal
