@echo off
setlocal
:: 터미널 출력 및 인자 전달 인코딩을 UTF-8로 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
:: ==============================================================================
:: Gemini-CLI HITL 2.0: Spec Drafting
:: ==============================================================================
::
:: +-----------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                          |
:: |  Available workers: spec, git, verify, context, scribe, audit               |
:: |  Usage: python scripts/gemini_worker.py <worker> "<instruction>" -c ...     |
:: |  << DIR CONTEXT >>: Dir path is allowed for -c (Auto-recurse all .py)       |
:: |  OUTPUT: design\gemini_output\spec_draft.md (or designated file)            |
:: +-----------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: [TD-007 Planning] Stress Test Config Automation & Migration
:: Task: Centralize Hardcoded Simulation Thresholds into config.py
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

echo [Gemini-CLI] Drafting Stress Test Config spec...
echo ============================================================

:: [COMMAND SLOT]
:: Target: TD-043 (Simulation God Class) - Action: DESIGN SPEC
set JOB_ID=TD-043_Simulation_SoC
python scripts/gemini_worker.py spec "Analyze `simulation/engine.py` which has become a God Class. Write a Zero-Question Implementation Spec to refactor it by extracting `AgentLifecycleManager` (handling agent creation, death, aging) and `SimulationInitializer` (handling setup). Use Composition/DI. The spec must include updated class diagrams, data flow, and precise pythonic pseudo-code. TARGET: `design/gemini_output/simulation_soc_spec.md`" -c simulation/engine.py > design\gemini_output\simulation_soc_spec.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini task completed successfully. Check design\gemini_output\
)
endlocal
