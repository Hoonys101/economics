@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0: PR Analysis (Track C+: WO-066 Pre-fix)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

:: [PR Drafting Task]
:: 브랜치: fix/sensory-architecture-dataflow-9343683714945509652
:: 상세 내용: "This commit resolves a critical bug in the Government AI's decision-making process where it was acting on stale, noisy data instead of the high-fidelity, smoothed sensory data provided by the simulation engine. The core issue was that the `Government` agent received the `GovernmentStateDTO` correctly but failed to pass it to its policy engine, `SmartLeviathanPolicy`. Instead, it passed the raw, single-tick `market_data`. This change corrects the data flow by ensuring `Government.make_policy_decision` passes the `self.sensory_data` DTO to the policy engine and updating `SmartLeviathanPolicy.decide` to accept and use the DTO. It also restores the AI's control over the `central_bank`."

python scripts/gemini_worker.py git "fix/sensory-architecture-dataflow-9343683714945509652 브랜치를 분석하여 PR 본문을 작성해줘. 1) Government.py와 SmartLeviathanPolicy.py 간의 데이터 흐름이 어떻게 수정되었는지 확인. 2) CentralBank 객체 전달이 복구되었는지 확인. 3) 이 변경이 WO-066의 목표(High-Fidelity)와 정합하는지, 그리고 기존 코드를 깨뜨리지 않는지(Regression) 검토." > design\gemini_output\last_run.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PR Analysis failed.
) else (
    echo [SUCCESS] PR Draft saved to design\gemini_output\last_run.md
)
endlocal
