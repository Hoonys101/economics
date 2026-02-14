@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Entry Point
python _internal/scripts/launcher.py gemini %*

endlocal
