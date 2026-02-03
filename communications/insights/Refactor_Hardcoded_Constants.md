# Refactoring Hardcoded Constants

## Context
Following the comprehensive audit report (`report_20260203_100435_당신은_클린_코드_전문가입니다__si.md`), we are undertaking a refactoring mission to externalize hardcoded constants found throughout the simulation codebase.

## Goal
To improve maintainability, testability, and configurability by moving hardcoded "magic numbers" into central configuration files (`config.py` and `config/economy_params.yaml`).

## Analysis of Targets
The audit identified constants in the following domains:
1.  **Bank & Finance:** Interest rates, margins, loan terms, and bankruptcy penalties.
2.  **Agent Behavior & AI:** Household demographics, AI parameters (epsilon decay, state discretization), and decision thresholds.
3.  **System & Policy:** Housing foreclosure discounts, M&A premiums, and policy actuator bounds.
4.  **Miscellaneous:** Labor mechanics, mortality rates, and market volatility windows.

## Technical Debt & Observations
*   **Duplication:** Some values like `TICKS_PER_YEAR` appear in `config.py` but might be hardcoded in `bank.py`, leading to potential sync issues.
*   **Configuration Split:** We have `config.py` (Python module) and `economy_params.yaml` (YAML). `config.py` often loads from `economy_params.yaml`. We need to ensure new YAML keys are correctly exposed via the `config` module if the code imports `config`.
*   **Testing:** Changing constants shouldn't break logic, but might break tests that assert specific return values based on those constants. Regression testing is crucial.

## Implementation Strategy
1.  **Update Configuration:** Add new keys to `economy_params.yaml` and `config.py`.
2.  **Refactor Code:** Replace literals with `config.PARAMETER_NAME`.
3.  **Verify:** Ensure no runtime errors and pass unit tests.
