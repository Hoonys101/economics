@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Manifest → JSON 동기화 실행
python _internal/scripts/launcher.py sync

endlocal
