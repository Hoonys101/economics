@echo off
setlocal
chcp 65001 > nul

echo 🧹 [Antigravity] Finalizing Session: Git Commit ^& Sanitation...

:: 1. Git Status Check
echo 📊 Checking changes...
git add .
git status --short

:: 2. Git Commit
echo 📝 Committing changes...
git commit -m "docs: finalize session, update architecture and handover"

:: 3. Run Sanitation (Directly integrate cleanup-session logic without pausing)
echo 🧼 Sanitizing temporary files...

:: Gemini Output Cleanup
if exist "design\_archive\gemini_output" (
    del /q "design\_archive\gemini_output\*.*" > nul 2>&1
)

:: Drafts Cleanup
if exist "design\3_work_artifacts\drafts" (
    del /q "design\3_work_artifacts\drafts\*.md" > nul 2>&1
)

:: Jules Logs Cleanup
if exist "communications\jules_logs" (
    del /q "communications\jules_logs\*.*" > nul 2>&1
)

:: Root and PR Debris
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

:: Temporary Repositories and Logs
del /q "reports\temp\report_*.md" > nul 2>&1
del /q "communications\insights\*.md" > nul 2>&1
del /q "design\command_registry.json.bak" > nul 2>&1

:: Temp Python Scripts
del /q temp_*.py > nul 2>&1

:: 4. Git Push
echo 🚀 Pushing to main branch...
git push origin main

echo ✅ Session officially closed. Workspace is in Cold Boot state.
endlocal
