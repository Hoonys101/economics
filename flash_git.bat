@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

set BRANCH=%1
if "%BRANCH%"=="" (
    echo Usage: flash_git.bat ^<branch_name^>
    exit /b 1
)

:: Sync check
echo 🔍 [Git-Review-Flash] Checking branch: %BRANCH%
python scripts/git_sync_checker.py %BRANCH%

:: Fetch
echo 📡 [Step 2] Fetching latest changes from origin/%BRANCH%...
git fetch origin %BRANCH%

:: Ensure output directory exists
if not exist "design\_archive\gemini_output" mkdir "design\_archive\gemini_output"

:: Diff generation
set DIFF_FILE=design\_archive\gemini_output\pr_diff_%BRANCH%.txt
echo 📝 [Step 3] Generating diff: main...FETCH_HEAD -^> %DIFF_FILE%
git diff main...FETCH_HEAD > "%DIFF_FILE%"

:: Gemini Review (Flash)
echo 🧠 [Step 4] Running AI Code Review (Model: FLASH)...
set REVIEW_FILE=design\_archive\gemini_output\pr_review_%BRANCH%.md

:: Execute review and capture both stdout and stderr to the review file
python scripts/gemini_worker.py git-review "Analyze this PR." -c "%DIFF_FILE%" --model flash > "%REVIEW_FILE%" 2>&1

echo ✅ Review complete. Report: %REVIEW_FILE%

endlocal
