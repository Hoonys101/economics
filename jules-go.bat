@echo off
setlocal
:: 터미널 출력 및 인자 전달 인코딩을 UTF-8로 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
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
:: |     (OR) send-message SESSION_ID --file "FILE_PATH"                     |
:: |  4. complete SESSION_ID                                                 |
:: |  5. get-session SESSION_ID                                              |
:: +-------------------------------------------------------------------------+
:: |  OUTPUT: communications\jules_logs\last_run.md                          |
:: +-------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: WO-072 (Sovereign Debt)
:: Action: Logic Review & Correction Dispatch
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "communications\jules_logs" (
    mkdir "communications\jules_logs"
)

echo [Jules-Bridge] Sending message to WO-072 session...
echo ----------------------------------------------------

:: [COMMAND SLOT]
:: Target: TD-044 (Household SoC) - Action: CREATE NEW SESSION
set TARGET="TD-044: Household God Class Refactoring"
set MISSION="REFACTOR `simulation/core_agents.py` following `design/gemini_output/household_soc_spec.md`. PATTERN: Same as TD-045 (Firm SoC). KEY CONSTRAINTS: 1. Household OWNS state (assets, inventory). Managers use `household.adjust_assets()` methods. 2. Use Facade pattern - external API unchanged. 3. Execution order: work -> consume -> pay_taxes. TASKS: 1. Create `simulation/components/economy_manager.py`. 2. Create `simulation/components/labor_manager.py`. 3. Household becomes coordinator. VERIFY: All tests in `tests/test_core_agents.py` must pass."

:: 1. Create Session & Send Initial Mission
python scripts/jules_bridge.py create %TARGET% %MISSION% > communications\jules_logs\last_run.md 2>&1

:: 2. Auto-Record to Session Ledger
:: echo ^| %DATE% ^| [NEW_SESSION] ^| TD-044 ^| SESSION STARTED ^| >> design\SESSION_LEDGER.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] WO-077 mission dispatched.
    echo [NOTE] Please check 'communications\jules_logs\last_run.md' for the Session ID.
    type communications\jules_logs\last_run.md
)
endlocal
