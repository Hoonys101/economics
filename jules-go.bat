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
:: Target: TD-024 Pytest Path Standardization (Full Restart)
:: Action: Create new Jules session with comprehensive context
python scripts/jules_bridge.py create "TD-024: Pytest Infrastructure Fix" "Mission: 완벽한 Pytest 환경 표준화 및 수집 에러 해결. Reference: design/specs/TD-024_pytest_path_fix_spec.md. Tasks: 1) Ensure pytest.ini is correctly configured in the root (pythonpath = .). 2) Remove sys.path hacks from tests/conftest.py. 3) CRITICAL: Fix 'pytest tests/' collection error (exit code 1). Run 'pytest --collect-only' to diagnose broken imports or configuration conflicts. 4) Verify all tests pass without ModuleNotFoundError. Reporting: Log all fixed errors in communications/insights/ upon completion." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
