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

:: Target: WO-037 (Simulation Cockpit) - Action: DISPATCH TO JULES
set JOB_ID=WO-037_Simulation_Cockpit
set INSTRUCTION="Implement WO-037 Simulation Cockpit. 1. Create 'dashboard/app.py' using code from 'design/specs/WO-037_Simulation_Cockpit_Spec.md'. 2. STRICTLY READ-ONLY. Import ONLY 'modules.analytics.loader.DataLoader'. 3. Verify by running 'streamlit run dashboard/app.py' (or check no import errors). 4. Do NOT modify 'loader.py' or 'engine.py'."

:: 1. Create Session
python scripts/jules_bridge.py create "WO-037 Simulation Cockpit" %INSTRUCTION% > communications\jules_logs\last_run.md 2>&1

:: 2. Auto-Record to Session Ledger
:: echo ^| %DATE% ^| [START] ^| WO-037 ^| Simulation Cockpit Dispatch ^| >> design\SESSION_LEDGER.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Jules Dispatch Complete.
    echo [NOTE] Check 'communications\jules_logs\last_run.md' for session ID.
    type communications\jules_logs\last_run.md
)
endlocal
