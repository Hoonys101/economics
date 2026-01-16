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
:: Target: WO-037 (Simulation Cockpit) - Action: DRAFT SPECIFICATION
set JOB_ID=WO-037_Simulation_Cockpit
python scripts/gemini_worker.py spec "Draft a Zero-Question Spec for 'WO-037: Simulation Cockpit (Dashboard)'. GOALS: 1. Create a Streamlit app in 'dashboard/app.py'. 2. Read ONLY from 'simulation_data.db' using 'modules/analytics/loader.py'. 3. Visualize Key Metrics: GDP (Real/Nominal), Inflation (CPI), Population, Gini Coefficient. 4. NO WRITE ACCESS to simulation core. TARGET: 'design/specs/WO-037_Simulation_Cockpit_Spec.md'. OUTPUT FORMAT: Strict Markdown." -c modules/analytics/loader.py design/roadmap.md -o design\specs\WO-037_Simulation_Cockpit_Spec.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini Task %JOB_ID% completed.
    echo [OUTPUT] Check design\specs\%JOB_ID%_Spec.md or work_orders\%JOB_ID%.md
)
endlocal
