@echo off
setlocal
chcp 65001 > nul

echo 🧹 Starting Tactical Sanitation...

:: 1. Gemini Output Cleanup
if exist "design\_archive\gemini_output" (
    echo    [-] Clearing Gemini Output...
    del /q "design\_archive\gemini_output\*.*" > nul 2>&1
)

:: 2. Drafts Cleanup
if exist "design\3_work_artifacts\drafts" (
    echo    [-] Clearing Artifact Drafts...
    del /q "design\3_work_artifacts\drafts\*.md" > nul 2>&1
)

:: 3. Jules Logs Cleanup
if exist "communications\jules_logs" (
    echo    [-] Clearing Jules Logs...
    del /q "communications\jules_logs\*.*" > nul 2>&1
)

:: 4. Root and PR Debris
echo    [-] Clearing Root and PR Debris...
del /q simulation.log > nul 2>&1
del /q leak_debug.txt > nul 2>&1
del /q pr_diff_*.txt > nul 2>&1
del /q pr_diff_*.md > nul 2>&1
del /q pr_review_*.md > nul 2>&1
del /q diagnose_report.txt > nul 2>&1
del /q leak_hunt_result.txt > nul 2>&1
del /q leak_report.txt > nul 2>&1
del /q remote_branches.txt > nul 2>&1
del /q branch_info*.txt > nul 2>&1
del /q remotes.txt > nul 2>&1
del /q iron_debug.log > nul 2>&1

:: 5. Temporary Repositories and Logs
echo    [-] Clearing Temp Reports and Insights...
del /q "reports\temp\report_*.md" > nul 2>&1
del /q "communications\insights\*.md" > nul 2>&1
del /q "design\command_registry.json.bak" > nul 2>&1

:: 6. Temp Python Scripts
del /q temp_*.py > nul 2>&1

echo ✅ Sanitation Complete. Workspace is now in Cold Boot state.
pause
