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
:: Target: WO-072 (Sovereign Debt) - Action: Core Logic Correction
:: 리뷰 결과(QE 조건, 상환 규약, 하드코딩)를 바탕으로 로직 수정을 지시합니다.
python scripts/jules_bridge.py send-message 7617648577093442794 "Review complete. I have identified 3 critical logic gaps in your WIP PR. Prioritize fixing these before worrying about the unit tests: 1) QE Violation: Limit Central Bank intervention only when yields exceed 10%. Currently, you are masking the Crowding Out effect. 2) Missing Covenant: Implement mandatory repayment (50% of profit) in the bailout loan logic. 3) New Hardcoding Debt: Refactor static bond maturity and risk premium tiers to use config constants. See 'design/gemini_output/pr_review_sovereign-debt-wip-7617648577093442794.md' for details. Fix the heart of the system first." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
