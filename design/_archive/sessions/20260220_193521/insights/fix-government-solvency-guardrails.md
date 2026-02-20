# Fix Government Solvency Guardrails

## Current Architectural State
The Government agent currently relies on `_issue_deficit_bonds` to cover shortfalls in welfare and other spending. While `FiscalBondService` attempts to find buyers, the agent's logic often defaults to "try to issue bonds, if it fails, stop spending". This provides a basic zero-sum check (no magic money unless a buyer exists), but lacks proactive solvency management.
Crucially, the `FiscalEngine` (the brain) does not account for the government's financial health when making decisions on tax rates, welfare budgets, or bailouts. It approves bailouts based solely on firm solvency/requests, potentially approving massive spending even when the government is deep in debt.

## Proposed Guardrails
To enforce "Zero-Sum Integrity" and "Solvency":
1.  **Debt Brake Logic in Fiscal Engine**:
    -   If `Debt/GDP > 1.5` (Debt Ceiling), the engine will force tax hikes and cut welfare spending to reduce the deficit.
    -   If `Debt/GDP > 1.0` (Warning Zone), welfare spending will be linearly reduced.
2.  **Bailout Restrictions**:
    -   Bailouts will be rejected if `Debt/GDP > 1.5`.
    -   Bailouts will be rejected if the government lacks sufficient liquid assets (unless it can confidently issue bonds, but for strict safety, we'll check assets first).
3.  **Strict Budget Constraints**:
    -   The `FiscalEngine` will receive the full `FiscalStateDTO` including assets and debt, allowing it to make informed trade-offs.

## Implementation Plan
-   Modify `modules/government/engines/fiscal_engine.py` to implement the Debt Brake logic.
-   Update `FiscalDecisionDTO` generation to reflect these constraints.
-   Add unit tests in `tests/modules/government/engines/test_fiscal_guardrails.py` to verify behavior under high debt scenarios.

## Test Evidence
(To be added after implementation)
\n## Test Evidence\n```\n
tests/modules/government/engines/test_fiscal_guardrails.py::TestFiscalGuardrails::test_debt_brake_welfare_reduction PASSED [ 20%]
tests/modules/government/engines/test_fiscal_guardrails.py::TestFiscalGuardrails::test_debt_brake_extreme_welfare_cut PASSED [ 40%]
tests/modules/government/engines/test_fiscal_guardrails.py::TestFiscalGuardrails::test_debt_brake_tax_hike_in_recession PASSED [ 60%]
tests/modules/government/engines/test_fiscal_guardrails.py::TestFiscalGuardrails::test_bailout_rejection_due_to_debt PASSED [ 80%]
tests/modules/government/engines/test_fiscal_guardrails.py::TestFiscalGuardrails::test_bailout_rejection_due_to_insufficient_funds PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 5 passed, 2 warnings in 0.24s =========================\n```
