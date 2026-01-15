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
:: Target: (Antigravity fills this dynamically)
:: Task: (Antigravity fills this dynamically)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

echo [Gemini-CLI] Drafting spec...
echo ============================================================

:: [COMMAND SLOT]
:: Target: Technical Debt Audit (Hardcoded/Rule-based)
:: Task: Identify all magic numbers and rigid heuristics.

python scripts/gemini_worker.py audit "Task: Identify all hardcoded magic numbers and rule-based heuristics across the codebase. Focus: 1) config.py: Arbitrary constants. 2) simulation/agents/: Hardcoded thresholds, fixed rates, and deterministic if/else decision logic. 3) simulation/systems/: Rigid formulas that should be adaptive. Output: A detailed list of Technical Debts (TD-XXX) with file paths, code snippets, and why they require re-planning for 'Adaptive AI Migration'." -c simulation/ config.py > design\gemini_output\audit_hardcoded_debt.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini task completed successfully. Check design\gemini_output\
)
endlocal
