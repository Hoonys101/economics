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
:: Target: TD-008 (Finance Upgrade) - Action: DRAFT SPECIFICATION
set JOB_ID=TD-008_Finance_Upgrade
python scripts/gemini_worker.py spec "Draft a Zero-Question Spec for 'TD-008: Advanced Finance System'. GOALS: 1. Implement 'Altman Z-Score' for firm valuation (replacing primitive asset check). 2. Convert Bailouts from Grants to 'Callable Loans' (Debt) with interest. 3. Define 'BailoutCovenant' class. TARGET: 'design/specs/TD-008_Finance_Upgrade_Spec.md'. OUTPUT FORMAT: Strict Markdown. No conversational filler." -c modules/finance/system.py simulation/firms.py -o design\specs\TD-008_Finance_Upgrade_Spec.md

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini Task %JOB_ID% completed.
    echo [OUTPUT] Check design\specs(%JOB_ID%_Spec.md) or work_orders(%JOB_ID%.md)
)
endlocal
