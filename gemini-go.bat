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
:: Target: WO-079 (Config Automation) - Action: DRAFT SPECIFICATION V2
set JOB_ID=WO-079_Config_Automation_v2
python scripts/gemini_worker.py spec "Draft a Zero-Question Spec for 'WO-079: Config Automation (v2)'. GOALS: 1. Implement 'simulation/config_manager.py' as a Leaf Node. 2. Use a Hybrid approach (YAML + legacy config.py fallbacks). 3. Organize constants into ai.yaml, finance.yaml, simulation.yaml. 4. MANDATORY: Provide a testing strategy to avoid breaking 80+ existing tests using monkeypatch. TARGET: 'design/specs/WO-079_Config_Automation_v2.md'." -c simulation/bank.py simulation/engine.py scripts/gemini_worker.py -a design/gemini_output/audit_preflight_WO-079.md -o design/specs/WO-079_Config_Automation_v2.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini Task %JOB_ID% completed.
    echo [OUTPUT] Check design\specs\%JOB_ID%_Spec.md or work_orders\%JOB_ID%.md
)
endlocal
