# 🔍 Git Diff Review: Fractional Reserve & Credit Scoring

## 🔍 Summary

This pull request introduces a sophisticated **Credit Scoring Service** and fundamentally shifts the banking model to **Fractional Reserve Banking**. Instead of lending existing assets, the bank now creates new money (deposits) when issuing loans, a core mechanic of modern economies. This change is propagated through the `Bank`, `LoanMarket`, and agent decision-making modules (`CorporateManager`, `HousingSystem`). The implementation is robust, featuring clear separation of concerns, dependency injection, and comprehensive new tests.

## 🚨 Critical Issues

None found. The code is clean of hardcoded keys, secrets, or absolute paths.

## ⚠️ Logic & Spec Gaps

1.  **Hardcoded Financial Assumptions in `HousingSystem`**:
    *   **File**: `simulation/systems/housing_system.py`
    *   **Lines**: `gross_income = buyer.current_wage * 8.0 * (100.0 / 12.0)` and `existing_debt_payments = total_debt * 0.01`
    *   **Issue**: The calculation for a household's monthly income (from wages) and the estimation of existing debt payments are based on hardcoded multipliers (`8.0`, `100.0 / 12.0`, `0.01`). These values represent significant economic assumptions and should not be magic numbers in the code. They are difficult to track, audit, and adjust.

## 💡 Suggestions

1.  **Configuration for Financial Assumptions**:
    *   **Recommendation**: Relocate the hardcoded multipliers from `housing_system.py` into the configuration files (e.g., `config/economy_params.yaml`). This makes the assumptions explicit, easily tunable for experiments, and improves the model's transparency.
    *   **Example**:
        ```yaml
        # in config/economy_params.yaml
        income_estimation:
          work_hours_per_tick: 8.0
          ticks_per_month_approx: 8.33 # (100 ticks/year / 12 months)
        debt_estimation:
          monthly_payment_rate_approx: 0.01
        ```

2.  **Zero-Income DTI Logic Simplification**:
    *   **File**: `modules/finance/credit_scoring.py`
    *   **Context**: The logic to handle `gross_income == 0` is slightly convoluted. While correct, it can be simplified. The `if profile["collateral_value"] <= 0:` check at the end already correctly denies any unsecured loan to a zero-income borrower, as `max_amount` will be zero.
    *   **Recommendation**: Consider simplifying the initial DTI calculation for the edge case of zero income. The current implementation is functional, but a more direct approach might improve readability. This is a minor stylistic suggestion.

## 🧠 Manual Update Proposal

*   **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
*   **Update Content**:

    ---
    ### **Concept: Fractional Reserve Banking & Endogenous Money**

    *   **Phenomenon**: The system has transitioned from a "loanable funds" model (banks lend out existing savings) to a "credit creation" model (banks create new money when they lend).
    *   **Mechanism**:
        1.  A borrower requests a loan.
        2.  The bank assesses creditworthiness (DTI, LTV ratios) via the `CreditScoringService`.
        3.  If approved, the bank checks if it has sufficient **reserves** (a fraction of the new deposit, e.g., 10%), not the full loan amount.
        4.  The bank creates a `Loan` asset on its books and simultaneously creates a `Deposit` liability of the same amount in the borrower's name. This deposit is **new money**.
        5.  The system's total money supply (tracked by `government.total_money_issued`) increases by the loan amount.
    *   **Implementation**:
        -   `simulation/bank.py`'s `grant_loan` method no longer decreases the bank's assets. It creates a new deposit via `deposit_from_customer`.
        -   The `CreditScoringService` (`modules/finance/credit_scoring.py`) acts as a gatekeeper, preventing reckless lending and managing systemic risk.
    *   **Lesson/Insight**: This change enables the money supply to dynamically expand and contract based on economic activity (demand for credit), which is a more realistic simulation of modern financial systems. It also introduces the critical risk of bank runs and the need for reserve requirements and central bank oversight.
    ---

## ✅ Verdict

**REQUEST CHANGES**

This is an excellent and architecturally sound implementation of a complex economic feature. The verdict is `REQUEST CHANGES` solely to address the minor but important issue of hardcoded financial assumptions in `housing_system.py`. Once these are moved to configuration, this PR is ready for approval.
