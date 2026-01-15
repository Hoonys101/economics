@echo off
setlocal
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
:: Antigravity injects the gemini_worker.py command here

python scripts/gemini_worker.py spec "WO-068: CPR System Enhancement Spec. Resolve TD-008 and TD-009. Goals: 1) Replace primitive valuation logic with Solvency/Liquidity metrics to avoid bailing out zombie firms. 2) Convert unconditional grants to Government Loans requiring repayment with interest. 3) Track fiscal impact of bailouts in Government.total_debt. Include: Data structures (BailoutRequestDTO, LoanContractDTO), pseudo-code for eligibility check, and test cases." -c simulation/systems/bootstrapper.py simulation/agents/government.py config.py > design\gemini_output\spec_draft.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Spec drafting failed.
) else (
    echo [SUCCESS] Spec draft saved to design\gemini_output\spec_draft.md
)
endlocal
