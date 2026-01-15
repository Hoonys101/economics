@echo off
setlocal
:: 터미널 출력 및 인자 전달 인코딩을 UTF-8로 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
:: ==============================================================================
:: Gemini-CLI HITL 2.0: Spec Drafting
:: ==============================================================================
::
:: +-------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                      |
:: |  Available workers: spec, git, verify, context, scribe                  |
:: |  Usage: python scripts/gemini_worker.py <worker> "<instruction>" -c ... |
:: |  OUTPUT: design\gemini_output\spec_draft.md                             |
:: +-------------------------------------------------------------------------+
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
:: Target: Phase 26.5 Sovereign Debt & Bailout Refactor
:: Task: Create Zero-Question Spec for National Debt and Loan-based CPR

python scripts/gemini_worker.py spec "Task: Create a detailed specification for 'Sovereign Debt & Corporate Bailout System'. Context: Currently, bailouts are free grants. We need to convert them to Senior Debt Loans and introduce Government Bonds (Sovereign Debt) to bridge fiscal deficits. Key Requirements: 1) CPR Refactor: AS-IS Grants -> TO-BE Interest-bearing Loans. Covenants: No dividends and executive salary freeze for debtors. 2) Solvency Check: Simplified Altman Z-Score (LiquidAssets, RetainedEarnings) to filter 'Zombie Firms'. 3) Bond Issuance: Market-driven bond yields acting as a benchmark. Roles of Banks, Households, and CB (QE). Include: Data structures (BondDTO, BailoutLoanDTO), pseudo-code for eligibility/issuance logic, and Phase 26 integration. Output: Markdown format." -c simulation/agents/government.py simulation/systems/bootstrapper.py simulation/agents/firm.py > design\gemini_output\spec_draft.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Spec drafting failed.
) else (
    echo [SUCCESS] Spec draft saved to design\gemini_output\spec_draft.md
)
endlocal
