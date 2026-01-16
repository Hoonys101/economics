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
:: Target: WO-077 (Root Cause Analysis) - Action: AUDIT ENGINE COMPLEXITY
set JOB_ID=Audit_Engine_Complexity
python scripts/gemini_worker.py audit "Analyze `simulation/engine.py` (specifically `__init__` and `run_tick`) and `tests/test_engine.py`. Determine if the high coupling and heavy initialization logic in `Simulation` are the root causes of the WO-077 test failures. Verify if separating `SimulationInitializer` (TD-043) is a necessary pre-requisite to fix the fragile tests. Output the analysis to `design/gemini_output/audit_engine_complexity.md`." -c simulation/engine.py tests/test_engine.py > design\gemini_output\audit_engine_complexity.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini audit failed. Check logs.
) else (
    echo [SUCCESS] Engine complexity audit completed. Check design\gemini_output\audit_engine_complexity.md
)
endlocal
