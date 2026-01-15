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
:: Target: Create WO-067 (Reaction Test)
:: Action: Dispatch new Jules session for verification
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "communications\jules_logs" (
    mkdir "communications\jules_logs"
)

echo [Jules-Bridge] Creating WO-067 session...
echo ----------------------------------------------------

:: [COMMAND SLOT]
python scripts/jules_bridge.py create "WO-067: High-Fidelity Reaction Test" "Implement the verification script as specified in design/work_orders/WO-067-Reaction-Test.md. Create scripts/verify_policy_reaction.py that: 1) Runs 100-tick burn-in, 2) Injects 15%% inflation shock via GovernmentStateDTO, 3) Verifies CentralBank.base_rate increases within 2 ticks. Success criteria: PASS if rate increases, FAIL otherwise. Report test output." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
