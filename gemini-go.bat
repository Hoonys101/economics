@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0: PR Analysis (Track C: WO-062)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

:: [PR Drafting Task]
:: 브랜치: feature/macro-linked-portfolio-14018014647659914271
:: 상세 내용: "This change implements the Macro-Linked Portfolio logic as specified in the work order. It introduces a new feature that dynamically adjusts household portfolio risk aversion based on macroeconomic conditions, gated by a feature flag. The implementation includes a new DTO for macroeconomic data, a VIX proxy for market volatility, and unit tests for the new logic. All code review feedback has been addressed."

python scripts/gemini_worker.py git "feature/macro-linked-portfolio-14018014647659914271 브랜치를 분석하여 PR 본문을 작성해줘. 1) PortfolioManager에 MacroFinancialContext 연동 여부, 2) 위험 회피도(Lambda) 동적 조정 로직의 적절성, 3) VIX proxy 구현 방식을 중점적으로 검토하고, TD-031(통화 무결성) 패치와 충돌 가능성이 있는지 확인해줘." > design\gemini_output\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PR Analysis failed.
) else (
    echo [SUCCESS] PR Draft saved to design\gemini_output\last_run.md
)
endlocal
