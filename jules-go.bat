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
:: Target: WO-077 (Config Automation) - Action: CREATE NEW SESSION
set TARGET="WO-077: Config Automation"
set MISSION="Implement Centralized Config System (TD-007). REFERENCE: Strictly follow the Zero-Question Spec in `design/gemini_output/stress_test_config_spec.md`. TASK: 1) Create `simulation/config.py` with `SimulationConfig` dataclass hierarchy. 2) Implement JSON profile loader. 3) Refactor `engine.py` and `firms.py` to use `sim_config` instead of hardcoded constants. 4) Create `test_config_loading.py` verification."

:: 1. Create Session & Send Initial Mission
:: Note: 'create' command now accepts (Title, Prompt) thanks to previous update
python scripts/jules_bridge.py create %TARGET% %MISSION% > communications\jules_logs\last_run.md 2>&1

:: 2. Auto-Record to Session Ledger (Append mode)
echo ^| %DATE% ^| %SESSION_ID% ^| %TARGET% ^| %MISSION% ^| >> design\SESSION_LEDGER.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] WO-076 mission dispatched and recorded to SESSION_LEDGER.md.
    type communications\jules_logs\last_run.md
)
endlocal
