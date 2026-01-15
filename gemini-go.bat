@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0: Drafting WO-065 (Monetary Integrity & Suture)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

:: [Track B Spec Drafting]
python scripts/gemini_worker.py spec "WO-065: Monetary Integrity & Suture 구현 명세 작성. 핵심 과제: 1) simulation/systems/inheritance_manager.py 수정: 상속 시 현금뿐만 아니라 은행 예금(bank.deposits)도 상속인에게 이전하거나 국고로 환수하는 로직 구현. 2) simulation/engine.py 수정: Tick 600 쇼크(자산 반토막) 시 감소한 자산만큼 government.total_money_destroyed에 합산하여 장부 동기화. 3) 가계 사망/기업 청산 시 남은 자금을 국고(Government Assets)로 귀속시키는 'Escheatment' 로직 보강. 4) 통화 정합성 검증 테스트 설계." -c simulation/systems/inheritance_manager.py simulation/engine.py simulation/bank.py > design\gemini_output\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Spec drafting failed.
) else (
    echo [SUCCESS] WO-065 Spec Draft saved to design\gemini_output\last_run.md
)
endlocal
