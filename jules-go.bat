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
:: |     - List all active Jules sessions                                    |
:: |     - Output: ID, Title, State, UpdateTime                              |
:: |                                                                         |
:: |  2. create "TITLE" "INSTRUCTION"                                        |
:: |     - Create new Jules session with task                                |
:: |     - Ex: create "WO-067: Test" "Please implement..."                   |
:: |                                                                         |
:: |  3. send-message SESSION_ID "MESSAGE"                                   |
:: |     - Send message/feedback to specific session                         |
:: |     - Ex: send-message 12345 "Fix the import error first."              |
:: |                                                                         |
:: |  4. complete SESSION_ID                                                 |
:: |     - Mark session as complete (updates team_assignments.json)          |
:: |     - Call after PR merge                                               |
:: |                                                                         |
:: |  5. get-session SESSION_ID                                              |
:: |     - Get detailed info of specific session                             |
:: |                                                                         |
:: +-------------------------------------------------------------------------+
:: |  WORKFLOW:                                                              |
:: |  1. Antigravity writes command in [COMMAND SLOT]                        |
:: |  2. USER runs .\jules-go.bat                                            |
:: |  3. Result saved to communications\jules_logs\last_run.md               |
:: |  4. Antigravity reviews result and decides next action                  |
:: +-------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: Jules Bravo (WO-065) - Monetary Integrity
:: Action: Check session status
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "communications\jules_logs" (
    mkdir "communications\jules_logs"
)

echo [Jules-Bridge] Executing command...
echo ----------------------------------------------------

:: [COMMAND SLOT]
:: Target: Jules Bravo (WO-065)
:: Action: Send complete rescue steps

python scripts/jules_bridge.py send-message 10296031762289509515 "STEP 1: Open simulation/agents/government.py. Find __init__ method. Add this line after 'self.total_money_issued = 0.0': self.total_money_destroyed = 0.0 --- STEP 2: Create file tests/test_wo065_minimal.py with this code: import math; from simulation.agents.government import Government; import config; gov = Government(id=999, initial_assets=0.0, config_module=config); gov.total_money_destroyed += 1000.0; assert math.isclose(gov.total_money_destroyed, 1000.0); print('PASS') --- STEP 3: Run: python tests/test_wo065_minimal.py --- Report the output." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
