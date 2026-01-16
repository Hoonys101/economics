@echo off
setlocal
:: Set terminal and argument encoding to UTF-8
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
:: Target: WO-079 (Config Automation)
:: Action: Test Failure Diagnosis
:: ==============================================================================

if not exist "communications\jules_logs" (
    mkdir "communications\jules_logs"
)

:: [COMMAND SLOT]
:: Target: Jules (Implementer) - Action: WO-079 v2 IMPLEMENTATION
set JOB_ID=WO-079_Config_Automation_v2
python scripts/jules_bridge.py create "WO-079_Config_Automation_v2" "Implement WO-079 v2: High-reliability Config Automation. MISSION: 1. Create 'modules/common/config_manager/impl.py' based on the spec. 2. Ensure NO circular dependencies (Leaf Node). 3. Implement Hybrid loading (YAML with legacy config.py fallbacks). 4. MANDATORY: Verify that existing tests still pass by providing the 'set_value_for_test' interface. TARGET_SPEC: 'design/specs/WO-079_Config_Automation_v2.md'. WORK_ORDER: 'design/work_orders/WO-079_Config_Automation_v2.md'." --wait > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Jules task (WO-079 v2) created.
    echo [NOTE] Check 'communications\jules_logs\last_run.md' for details.
    type communications\jules_logs\last_run.md
)
endlocal
