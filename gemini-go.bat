@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0: PR Analysis & Drafting (Track A: WO-064)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

:: [PR Drafting Task]
:: 브랜치: feature/banking-credit-engine-7095675393629273222
:: 상세 내용: "This commit introduces a fractional-reserve banking system, enabling credit creation within the simulation. The new `grant_loan` logic in `simulation/bank.py` now uses the `RESERVE_REQ_RATIO` from `config.py` when `GOLD_STANDARD_MODE` is disabled. The changes have been verified using the `scripts/verify_banking.py` script, which confirms a money multiplier greater than 1 and ensures bank solvency."

python scripts/gemini_worker.py git "feature/banking-credit-engine-7095675393629273222 브랜치의 작업 내용을 분석하고, 제공된 설명을 바탕으로 정식 Pull Request(PR) 본문을 작성해줘. 변경된 파일들의 SoC 준수 여부와 기술적 무결성을 검토하고, main 브랜치와의 병합 적합성을 평가해줘." > design\gemini_output\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PR Analysis failed.
) else (
    echo [SUCCESS] PR Draft saved to design\gemini_output\last_run.md
)
endlocal
