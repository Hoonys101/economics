@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

echo ==========================================
echo 🏁 SESSION CONCLUSION AUTOMATION
echo ==========================================

echo 🌾 [Step 1] Harvesting Insights and Generating Handover...
python _internal/scripts/session_manager.py

echo.
echo 📋 [Step 2] Updates suggested for:
echo    - design/1_governance/project_status.md
echo    - design/2_operations/ledgers/TECH_DEBT_LEDGER.md
echo.

set /p CLEAN="🧹 [Step 3] Run cleanup-session.bat now? (y/n): "
if /i "%CLEAN%"=="y" (
    echo 🧼 Cleaning up temporary files...
    call cleanup-session.bat
)

echo.
echo ✅ Session successfully processed. 
echo 💡 Recommendation: Commit all changes with 'docs: update handover and architecture'
echo ==========================================
endlocal
