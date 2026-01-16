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
:: Target: WO-073 (Finance Refactor) - Action: FIX ATOMICITY BUG
set SESSION_ID=11970536560282331303
set TARGET=WO-073 (Atomicity)
set MISSION="CRITICAL BUG FOUND: 'Money Duplication' due to lack of atomicity in `_transfer`. Current implementation allows creditor to receive full amount even if debtor's withdraw() is capped by max(0, ...). TASK: 1) Update `IFinancialEntity.withdraw` to raise an `InsufficientFundsError` if funds are insufficient. 2) Refactor `_transfer` to use a try-except block: only call .deposit() if .withdraw() succeeds without error. 3) Ensure consistency across all entities (Bank, Firm, Gov). This is the final step to guarantee monetary integrity."

:: 1. Send Message to Jules
python scripts/jules_bridge.py send-message %SESSION_ID% %MISSION% > communications\jules_logs\last_run.md 2>&1

:: 2. Auto-Record to Session Ledger (Append mode)
:: Windows %DATE% variable usage (Locale dependent, but works for logging)
echo ^| %DATE% ^| %SESSION_ID% ^| %TARGET% ^| %MISSION% ^| >> design\SESSION_LEDGER.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Atomic transfer instruction sent and recorded.
    type communications\jules_logs\last_run.md
)
endlocal
