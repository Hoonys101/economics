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
:: Target: TD-044 (Household SoC) - Action: DESIGN SPEC (Auto-Audit Enabled)
set JOB_ID=TD-044_Household_SoC
python scripts/gemini_worker.py spec "Analyze `simulation/core_agents.py`. The `Household` class is a God Class mixing demographics, labor, and consumption logic. Write a Zero-Question Implementation Spec to refactor it using Composition. Extract `EconomyManager` (consumption, savings, tax) and `LaborManager` (work, skill, job search). `Household` should remain the identity/coordinator. The spec MUST address risks identified by the Auto-Audit. TARGET: `design/gemini_output/household_soc_spec.md`" -c simulation/core_agents.py > design\gemini_output\household_soc_spec.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini spec drafting with Auto-Audit completed. Check design\gemini_output\household_soc_spec.md
)
endlocal
