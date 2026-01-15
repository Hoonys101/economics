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
:: Target: WO-072 (Phase 26.5)
:: Action: Implement Sovereign Debt & Bailout Finance System
python scripts/jules_bridge.py create "WO-072: Sovereign Debt & Financial Credit" "Mission: '공짜 점심'의 시대를 끝내고 부채 기반의 책임 경제를 구축하라. Reference: design/specs/SOVEREIGN_DEBT_SPEC.md. Tasks: 1) modules/finance/api.py에 DTO 및 인터페이스 정의. 2) Altman Z-Score 기반 솔벤시 체크 구현 (Startup Grace Period 준수). 3) 국채 발행 및 시장 금리 형성 로직 구현. 4) 구제금융을 보조금에서 이자부 대출로 전환하라. Success Criteria: Z-Score 1.81 미만의 좀비 기업 퇴출 및 국채 금리에 따른 자금 위축(Crowding out) 증명. Reporting: insights/에 mass liquidation 리스크 보고." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
