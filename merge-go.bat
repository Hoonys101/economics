@echo off
setlocal
:: ==============================================================================
:: Auto Merger - Safe & Fast Integration
:: ==============================================================================

if "%1"=="" (
    echo [USAGE] merge-go.bat ^<Remote_Branch_Name^>
    echo Example: merge-go.bat WO-065-jury-restoration-12345
    exit /b 1
)

set TARGET_BRANCH=%1

echo.
echo 🚀 Starting Merge Sequence for: %TARGET_BRANCH%
echo --------------------------------------------------

:: 1. Checkout Main & Update
echo [1/4] Updating Main...
git checkout main
git pull origin main

:: 2. Check if branch exists
git ls-remote --exit-code --heads origin %TARGET_BRANCH% > nul
if %errorlevel% neq 0 (
    echo ❌ Error: Remote branch '%TARGET_BRANCH%' not found.
    exit /b 1
)

:: 3. Merge
echo.
echo [2/4] Merging Branch...
git merge origin/%TARGET_BRANCH% --no-edit
if %errorlevel% neq 0 (
    echo ❌ Merge Conflict Detected!
    echo    Please resolve conflicts manually, then commit and push.
    exit /b 1
)

:: 4. Push to Main
echo.
echo [3/4] Pushing to Main...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Failed to push to main. Check your network or permissions.
    exit /b 1
)

:: 5. Cleanup (Remote Branch)
echo.
echo [4/4] Cleaning up Remote Branch...
git push origin --delete %TARGET_BRANCH%

echo.
echo ✅ MERGE SUCCESS: %TARGET_BRANCH% -> main
echo 🛡️ The code is now integrated and the branch is deleted.
echo.
