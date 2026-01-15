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
:: Target: WO-068 (Phase 26 Step 1)
:: Action: Implement Macro-Linked Portfolio Decisions for Households
python scripts/jules_bridge.py create "WO-068: Macro-Linked Portfolio" "Mission: 에이전트들에게 '거시 경제의 눈(Macro Context)'을 가르쳐라. Reference: design/drafts/draft_Phase_26_Step_1__Link_Macro_Si.md. Tasks: 1) MacroFinancialContext DTO 구현하여 거시 지표 전달 케이퍼빌리티 확보. 2) 거시 스트레스에 따른 위험 회피 성향(Risk Aversion) 동적 조절 로직 구현. 3) Stagflation 시나리오에서 Safety Preference가 급증하는지 테스트로 증명하라. Reporting: 매크로 민감도 가중치 등 튜닝 인사이트를 communications/insights/에 상세히 기록할 것." > communications\jules_logs\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Command failed. Check logs.
) else (
    echo [SUCCESS] Command executed. Output:
    type communications\jules_logs\last_run.md
)
endlocal
