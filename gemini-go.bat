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
:: Target: W-1 Redesign - Double-Entry Bookkeeping Refactoring Spec
:: Task: Create Zero-Question Spec for Finance Module refactoring
python scripts/gemini_worker.py spec "Write a Zero-Question Implementation Spec for refactoring `modules/finance/system.py` to enforce Double-Entry Bookkeeping. REQUIREMENTS: 1) Replace one-way `grant()` with bidirectional `transfer(debtor, creditor, amount)` pattern. 2) Fix `grant_bailout_loan`: add `firm.cash_reserve += amount` after government deduction. 3) Fix `issue_treasury_bonds` QE path: add `central_bank.assets['cash'] -= amount` when CB purchases bonds. 4) All monetary ops must have explicit DEBTOR and CREDITOR. Include: Data Flow Diagram, Pseudo-code, Test Cases. Output in Korean." -c modules/finance/system.py modules/finance/api.py design/specs/SOVEREIGN_DEBT_SPEC.md reports/temp/report_20260116_073516_Analyze__modules_fin.md > design\gemini_output\double_entry_refactor_spec.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini task completed successfully. Check design\gemini_output\
)
endlocal
