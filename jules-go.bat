@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: 1) Manifest → JSON 자동 동기화
python _internal/scripts/launcher.py sync

:: 2) 실행
if "%~1" neq "" (
    python _internal/scripts/launcher.py jules %*
) else (
    python _internal/scripts/run_jules_interactive.py
)

endlocal
