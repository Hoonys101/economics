@echo off
setlocal
:: ==============================================================================
:: Jules-CLI Bridge 1.0: Agent Command Interface (HITL 2.0)
:: ==============================================================================
::
:: +-------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                      |
:: |  This file is modified by Antigravity. USER just runs it.               |
:: +-------------------------------------------------------------------------+
:: |  AVAILABLE COMMANDS (jules_bridge.py):                                  |
:: |                                                                         |
:: |  1. list-sessions --summary                                             |
:: |  2. create "TITLE" "INSTRUCTION"                                        |
:: |  3. send-message SESSION_ID "MESSAGE"                                   |
:: |  4. complete SESSION_ID                                                 |
:: |  5. get-session SESSION_ID                                              |
:: +-------------------------------------------------------------------------+
:: |  OUTPUT: communications\jules_logs\last_run.md                          |
:: +-------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: TD-024 (Pytest Path Fix) - Phase 26 Pre-requisite
:: Action: Jules Warm-up Task
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "communications\jules_logs" (
    mkdir "communications\jules_logs"
)

echo [Jules-Bridge] Creating TD-024 session...
echo ----------------------------------------------------

:: [COMMAND SLOT]
:: Target: TD-024 Post-Fix Stabilization
python scripts/jules_bridge.py create "TD-024: Post-Fix Test Stabilization" "Mission: Fix test collection and execution errors occurring after merging TD-024 (pytest.ini migration). Currently, 'pytest tests/' fails with exit code 1. Tasks: 1) Run 'pytest tests/ --collect-only' to diagnose collection errors (ImportErrors, etc.). 2) Fix broken test files or remaining path conflicts in conftest.py. 3) Ensure all tests are collected properly and at least core tests (engine, agents) pass. Reporting: Report details of fixed errors to communications/insights/." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
