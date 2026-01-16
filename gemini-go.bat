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
:: Target: W-1 Design - Config-driven Stress Test & Threshold Migration
:: Task: Create Zero-Question Spec for TD-007
python scripts/gemini_worker.py spec "Write a Zero-Question Implementation Spec for fixing TD-007 (Industrial Revolution Stress Test Config). GOAL: Identify all hardcoded 'magic numbers' related to economic thresholds (demand caps, supply floor, wage stickiness) across the simulation engine and move them to a centralized `config.py` structure. IMPLEMENTATION: 1) Propose a hierarchical Config Class structure. 2) Define a migration map for `simulation/engine.py` and `simulation/firms.py`. 3) Design a 'Stress Test Profile' loader that can override multiple config values at once for scenarios like the Industrial Revolution. Include: Config Schema, Migration Pseudo-code, and Scenario Loading Logic in Korean." -c config.py simulation/engine.py simulation/firms.py design/TECH_DEBT_LEDGER.md > design\gemini_output\stress_test_config_spec.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini task completed successfully. Check design\gemini_output\
)
endlocal
