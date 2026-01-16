@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: ==============================================================================
:: Inbound Report Harvester 1.0
:: ==============================================================================
:: This tool scans remote branches (refactor-*, observer-*, audit-*) 
:: and automatically pulls new .md reports into reports/inbound/
:: ==============================================================================

echo [Harvester] Starting scan for inbound reports...
echo ----------------------------------------------------

python scripts/report_harvester.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Harvester execution failed.
) else (
    echo ----------------------------------------------------
    echo [SUCCESS] Harvesting complete. 
    echo Check 'reports/inbound/' for new files.
    echo Check 'design/INBOUND_REPORTS.md' for sync log.
)

endlocal
