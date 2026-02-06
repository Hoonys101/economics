@echo off
echo 🦅 [Watchtower] Initiating Routine Project Audit...
python scripts/audit_watchtower.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Audit Cycle Complete. Summary generated in reports/audits/WATCHTOWER_SUMMARY.md
) else (
    echo.
    echo ❌ Audit Failed. Please check logs for details.
)
pause
