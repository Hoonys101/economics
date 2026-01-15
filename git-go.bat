@echo off
setlocal
:: ==============================================================================
:: Git-Go: PR Analysis Automation (HITL 2.0)
:: ==============================================================================
::
:: +-------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                      |
:: |  This script automates the PR review process.                           |
:: +-------------------------------------------------------------------------+
:: |  USAGE:                                                                 |
:: |    git-go.bat <BRANCH_NAME> [ANALYSIS_INSTRUCTION]                      |
:: |                                                                         |
:: |  EXAMPLES:                                                              |
:: |    git-go.bat feature/banking-credit-engine-123456                      |
:: |    git-go.bat fix/sensory-dataflow-789 "Check SoC compliance"           |
:: |                                                                         |
:: |  PIPELINE:                                                              |
:: |    Step 1: git fetch origin <branch>                                    |
:: |    Step 2: git diff main..origin/<branch> > diff file                   |
:: |    Step 3: gemini_worker.py git <instruction> -c <diff file>            |
:: |    Step 4: Output saved to design/gemini_output/                        |
:: +-------------------------------------------------------------------------+
::
:: ==============================================================================
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

:: Check for required argument
if "%~1"=="" (
    echo [ERROR] Branch name required.
    echo.
    echo [Usage] git-go.bat ^<BRANCH_NAME^> [ANALYSIS_INSTRUCTION]
    echo.
    echo Examples:
    echo   git-go.bat feature/banking-credit-engine-123456
    echo   git-go.bat fix/sensory-fix-789 "Verify data flow changes"
    exit /b 1
)

set BRANCH_NAME=%~1
set AUDIT_INSTRUCTION=%~2

:: Default instruction if not provided
if "%AUDIT_INSTRUCTION%"=="" (
    set AUDIT_INSTRUCTION=Analyze this PR. Check implementation completeness, test coverage, SoC compliance, and potential regressions.
)

:: Extract short name for output file (last part of branch name)
for %%i in ("%BRANCH_NAME%") do set SHORT_NAME=%%~ni

echo [Git-Go] PR Analysis Automation
echo ============================================================
echo [Branch] %BRANCH_NAME%
echo [Instruction] %AUDIT_INSTRUCTION%
echo ============================================================

:: Ensure output directory exists
if not exist "design\gemini_output" mkdir "design\gemini_output"

echo.
echo.
echo [Step 1] Syncing with Remote & Finding Head...
:: Capture the output directly into LATEST_COMMIT variable
for /f "delims=" %%i in ('python scripts/git_sync_checker.py %BRANCH_NAME%') do set LATEST_COMMIT=%%i

if "%LATEST_COMMIT%"=="" (
    echo [ERROR] Failed to sync and find latest commit.
    exit /b 1
)

echo [Target Commit] %LATEST_COMMIT%

echo.
echo [Step 2] Generating diff (main vs %LATEST_COMMIT%)...
git diff main..%LATEST_COMMIT% > design\gemini_output\pr_diff_%SHORT_NAME%.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to generate diff.
    exit /b 1
)

echo.
echo [Step 3] Running Gemini Analysis...
python scripts/gemini_worker.py git "%AUDIT_INSTRUCTION%" -c design\gemini_output\pr_diff_%SHORT_NAME%.txt > design\gemini_output\pr_review_%SHORT_NAME%.md 2>&1

echo.
echo ============================================================
echo [SUCCESS] Analysis Complete!
echo.
echo [Diff] design\gemini_output\pr_diff_%SHORT_NAME%.txt
echo [Review] design\gemini_output\pr_review_%SHORT_NAME%.md
echo.
echo [Next Steps]
echo   1. Review: type design\gemini_output\pr_review_%SHORT_NAME%.md
echo   2. Checkout: git checkout %BRANCH_NAME%
echo   3. Merge: git checkout main ^&^& git merge origin/%BRANCH_NAME% --no-edit
echo ============================================================
endlocal
