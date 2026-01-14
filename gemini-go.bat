@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0 Git Execution Runner (Remote Sync Version)
:: ==============================================================================
echo 🚀 Executing Git Sync, Merge & Cleanup Routine...

:: 1. Stage and Commit local changes in feature branch
echo 📝 Staging changes in feature branch...
git add .
git commit -m "feat(WO-060): complete stock market activation and finalized design docs"

:: 2. Switch to main and pull latest remote changes
echo 🔄 Switching to main and pulling latest from remote...
git checkout main
git pull origin main --rebase

:: 3. Merge feature branch into updated main
echo 🔄 Merging feature branch into main...
:: Note: Using full branch name from git status check
git merge feature/WO-060-stock-market-15007179683109829611 --no-edit

:: 4. Push combined results to remote
echo ⬆️ Pushing merged main to origin...
git push origin main

:: 5. Cleanup local feature branch
echo 🧹 Cleaning up temporary branch...
git branch -d feature/WO-060-stock-market-15007179683109829611

echo ✅ Git Sync & Merge Completed. Current branch:
git branch --show-current

endlocal
